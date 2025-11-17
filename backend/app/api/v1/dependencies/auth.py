"""
Authentication dependencies for FastAPI routes.

These dependencies handle token extraction, verification, and user loading.
"""

from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.logging_config import get_logger
from app.db.session import get_db

logger = get_logger(__name__)
from app.models.user import User
from app.services.user_service import user_service


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Extract and verify the JWT token, returning the user ID.

    This is the most basic auth dependency that just verifies the token
    and returns the user ID.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        User UUID

    Raises:
        HTTPException: If token is missing or invalid
    """
    token = credentials.credentials

    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify and decode JWT token
    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from payload
    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        logger.warning("Invalid user ID format in token: %s", user_id_str)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Extract and verify the JWT token, returning the full payload.

    Use this when you need access to more than just the user ID,
    such as token type, expiration, etc.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        Complete token payload with all claims

    Raises:
        HTTPException: If token is missing or invalid
    """
    token = credentials.credentials

    if not token:
        logger.warning("Missing authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    if not payload:
        logger.warning("Invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the database.

    This dependency verifies the JWT token, extracts the user ID,
    and loads the corresponding User record from the database.

    Args:
        user_id: User UUID from token (injected by get_current_user_id)
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If user cannot be loaded
    """
    try:
        # Get user by ID
        user = await user_service.get_by_id(
            db=db,
            user_id=user_id
        )

        if not user:
            logger.error("User not found for ID: %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            logger.warning("Inactive user attempted to authenticate: %s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        logger.debug("User authenticated successfully: %s", user.id)
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error loading user: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load user profile"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and verify they are active.

    This is an alias for get_current_user since that already checks
    for active status. Kept for semantic clarity.

    Args:
        current_user: Current user (injected by get_current_user)

    Returns:
        Active user instance
    """
    return current_user


async def require_guest_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require that the current user has guest role.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if they have guest role

    Raises:
        HTTPException: If user is not a guest
    """
    if not current_user.is_guest:
        logger.warning("User %s attempted to access guest-only endpoint", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires guest role"
        )

    return current_user


async def require_host_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require that the current user has host role.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if they have host role

    Raises:
        HTTPException: If user is not a host
    """
    if not current_user.is_host:
        logger.warning("User %s attempted to access host-only endpoint", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires host role"
        )

    return current_user


async def require_admin_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require that the current user has admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User instance if they are an admin

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logger.warning("User %s attempted to access admin-only endpoint", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires admin privileges"
        )

    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, or None if not.

    This is useful for endpoints that can be accessed both with and without
    authentication, where authentication provides additional features.

    Args:
        credentials: Optional HTTP Bearer token
        db: Database session

    Returns:
        User instance if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        payload = clerk_auth.verify_token(token)
        user = await user_service.get_or_create_by_clerk_id(
            db=db,
            clerk_user_id=payload.sub
        )
        return user if user and user.is_active else None
    except Exception as e:
        logger.debug("Optional auth failed: %s", str(e))
        return None
