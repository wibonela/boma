"""
Authentication endpoints.

Handles user registration, login, password reset, and token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.core.logging_config import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    PasswordChange,
    PasswordReset,
    PasswordResetRequest,
    Token,
    TokenRefresh,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import auth_service

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Registration & Login
# ============================================================================


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Register a new user with email and password.

    Creates a new user account and automatically creates a guest profile.
    Returns the user data (without sensitive fields).

    Requirements:
    - Email must be unique and valid
    - Phone number must be unique and in Tanzania format
    - Password must be at least 8 characters with uppercase, lowercase, and digit
    - Full name must be at least 2 characters

    Raises:
        400: Email or phone number already registered
        422: Validation errors
    """
    try:
        user = await auth_service.register_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            phone_number=user_data.phone_number,
            full_name=user_data.full_name,
            role=user_data.role or "guest",
        )

        logger.info("User registered successfully: %s", user.id)

        # Convert to response model
        return UserResponse(
            id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            full_name=user.full_name,
            email_verified=user.email_verified,
            is_active=user.is_active,
            role="guest" if user.is_guest and not user.is_host else "host" if user.is_host and not user.is_guest else "both",
            created_at=user.created_at.isoformat() if user.created_at else "",
        )

    except ValueError as e:
        logger.warning("Registration failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate with email and password.

    Returns JWT access token (30 min expiry) and refresh token (7 days expiry).

    Raises:
        401: Invalid credentials or inactive account
    """
    user = await auth_service.authenticate_user(
        db=db,
        email=credentials.email,
        password=credentials.password,
    )

    if not user:
        logger.warning("Login failed for email: %s", credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    await db.commit()

    # Create tokens
    tokens = auth_service.create_user_tokens(user.id)

    logger.info("User logged in successfully: %s", user.id)

    return Token(**tokens)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Refresh an access token using a valid refresh token.

    Returns a new access token (30 min expiry). The refresh token remains valid.

    Raises:
        401: Invalid or expired refresh token
    """
    new_token = await auth_service.refresh_access_token(
        db=db,
        refresh_token=token_data.refresh_token,
    )

    if not new_token:
        logger.warning("Token refresh failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Access token refreshed successfully")

    # Return new access token (keep same refresh token)
    return Token(
        access_token=new_token["access_token"],
        refresh_token=token_data.refresh_token,  # Return original refresh token
        token_type=new_token["token_type"],
        expires_in=new_token["expires_in"],
    )


# ============================================================================
# Password Management
# ============================================================================


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request a password reset email.

    Generates a password reset token and stores it in the database.
    In production, this would trigger an email with a reset link.

    For security, this endpoint always returns success even if the email
    doesn't exist (to prevent email enumeration attacks).

    Returns:
        Success message (always, regardless of whether email exists)
    """
    reset_token = await auth_service.initiate_password_reset(
        db=db,
        email=reset_request.email,
    )

    if reset_token:
        await db.commit()
        logger.info("Password reset requested for email: %s", reset_request.email)
        # TODO: Send email with reset token
        # In production: send_password_reset_email(reset_request.email, reset_token)

    # Always return success to prevent email enumeration
    return {
        "message": "If the email exists, a password reset link has been sent",
        # In development/testing, return the token (remove in production)
        "reset_token": reset_token if reset_token else None,
    }


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Confirm password reset with token and new password.

    Validates the reset token and updates the user's password.

    Raises:
        400: Invalid or expired token
    """
    success = await auth_service.reset_password(
        db=db,
        token=reset_data.token,
        new_password=reset_data.new_password,
    )

    if not success:
        logger.warning("Password reset failed with invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    await db.commit()

    logger.info("Password reset successfully")

    return {"message": "Password has been reset successfully"}


@router.post("/password/change", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Change password for authenticated user.

    Requires the current password for verification before setting new password.

    Raises:
        400: Incorrect current password
        401: Not authenticated
    """
    success = await auth_service.change_password(
        db=db,
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    if not success:
        logger.warning("Password change failed for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    await db.commit()

    logger.info("Password changed successfully for user %s", current_user.id)

    return {"message": "Password has been changed successfully"}


# ============================================================================
# Current User Info
# ============================================================================


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current authenticated user information.

    Returns basic user data for the authenticated user.
    """
    logger.info("User %s requested their info", current_user.id)

    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        phone_number=current_user.phone_number,
        full_name=current_user.full_name,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        role="guest" if current_user.is_guest and not current_user.is_host else "host" if current_user.is_host and not current_user.is_guest else "both",
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )
