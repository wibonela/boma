"""
Authentication service layer.

Business logic for user authentication, registration, and password management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from app.models.user import User, GuestProfile
from app.models.enums import UserStatus

logger = get_logger(__name__)


class AuthService:
    """Service for authentication-related business logic."""

    async def register_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        phone_number: str,
        full_name: str,
        role: str = "guest",
        country_code: str = None,
    ) -> User:
        """
        Register a new user with email and password.

        Args:
            db: Database session
            email: User email address
            password: Plain text password (will be hashed)
            phone_number: User phone number (Tanzania format)
            full_name: User's full name
            role: User role (guest, host, or both)
            country_code: ISO country code (defaults to settings.DEFAULT_COUNTRY)

        Returns:
            Created User instance

        Raises:
            ValueError: If email or phone already exists
        """
        # Check if email already exists
        existing_email = await self.get_by_email(db, email)
        if existing_email:
            raise ValueError("Email already registered")

        # Check if phone already exists
        existing_phone = await self.get_by_phone(db, phone_number)
        if existing_phone:
            raise ValueError("Phone number already registered")

        # Set default country
        if country_code is None:
            country_code = settings.DEFAULT_COUNTRY

        # Determine roles
        is_guest = role in ["guest", "both"]
        is_host = role in ["host", "both"]

        # Hash password
        password_hash = get_password_hash(password)

        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
            full_name=full_name,
            country_code=country_code,
            is_guest=is_guest,
            is_host=is_host,
            is_admin=False,
            status=UserStatus.ACTIVE,
            email_verified=False,  # Will be verified via email
            phone_verified=False,  # Will be verified via SMS/OTP
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        logger.info("Registered new user: %s (email=%s)", user.id, email)

        # Auto-create guest profile if guest role
        if is_guest:
            await self._create_guest_profile(db, user.id)
            logger.info("Auto-created guest profile for user: %s", user.id)

        await db.commit()

        return user

    async def authenticate_user(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate a user with email and password.

        Args:
            db: Database session
            email: User email address
            password: Plain text password to verify

        Returns:
            User instance if credentials are valid, None otherwise
        """
        # Get user by email
        user = await self.get_by_email(db, email)
        if not user:
            logger.warning("Authentication failed: user not found for email %s", email)
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning("Authentication failed: invalid password for email %s", email)
            return None

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            logger.warning("Authentication failed: user %s is not active (status: %s)", user.id, user.status)
            return None

        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        await db.flush()

        logger.info("User authenticated successfully: %s (email=%s)", user.id, email)

        return user

    def create_user_tokens(self, user_id: UUID) -> Dict[str, Any]:
        """
        Create access and refresh tokens for a user.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with access_token, refresh_token, token_type, and expires_in
        """
        # Convert UUID to string for JWT payload
        user_id_str = str(user_id)

        # Create tokens
        access_token = create_access_token(data={"sub": user_id_str})
        refresh_token = create_refresh_token(data={"sub": user_id_str})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes in seconds
        }

    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token using a valid refresh token.

        Args:
            db: Database session
            refresh_token: Refresh token string

        Returns:
            New token dictionary or None if refresh token is invalid
        """
        # Decode and validate refresh token
        payload = decode_token(refresh_token)
        if not payload:
            logger.warning("Invalid refresh token provided")
            return None

        # Verify token type
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None

        # Extract user ID
        user_id_str = payload.get("sub")
        if not user_id_str:
            logger.warning("Refresh token missing user ID")
            return None

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            logger.warning("Invalid user ID in refresh token: %s", user_id_str)
            return None

        # Verify user still exists and is active
        user = await self.get_by_id(db, user_id)
        if not user or user.status != UserStatus.ACTIVE:
            logger.warning("User %s not found or inactive", user_id)
            return None

        # Create new access token
        access_token = create_access_token(data={"sub": user_id_str})

        logger.info("Access token refreshed for user: %s", user_id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
        }

    async def initiate_password_reset(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[str]:
        """
        Initiate password reset flow for a user.

        Args:
            db: Database session
            email: User email address

        Returns:
            Password reset token if user exists, None otherwise
        """
        user = await self.get_by_email(db, email)
        if not user:
            # Don't reveal if email exists or not (security best practice)
            logger.warning("Password reset requested for non-existent email: %s", email)
            return None

        # Create reset token
        reset_token = create_password_reset_token(email)

        # Store token in database (for additional validation)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow()  # Token expiry is in JWT, but we track it here too
        await db.flush()

        logger.info("Password reset initiated for user: %s", user.id)

        return reset_token

    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Reset user password using a valid reset token.

        Args:
            db: Database session
            token: Password reset token
            new_password: New plain text password (will be hashed)

        Returns:
            True if password was reset successfully, False otherwise
        """
        # Verify token and extract email
        email = verify_password_reset_token(token)
        if not email:
            logger.warning("Invalid or expired password reset token")
            return False

        # Get user
        user = await self.get_by_email(db, email)
        if not user:
            logger.warning("User not found for password reset: %s", email)
            return False

        # Verify stored token matches (additional security check)
        if user.reset_token != token:
            logger.warning("Reset token mismatch for user: %s", user.id)
            return False

        # Hash new password
        password_hash = get_password_hash(new_password)

        # Update password and clear reset token
        user.password_hash = password_hash
        user.reset_token = None
        user.reset_token_expires = None
        await db.flush()

        logger.info("Password reset successfully for user: %s", user.id)

        return True

    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change password for an authenticated user.

        Args:
            db: Database session
            user_id: User UUID
            current_password: Current plain text password (for verification)
            new_password: New plain text password (will be hashed)

        Returns:
            True if password was changed successfully, False otherwise
        """
        user = await self.get_by_id(db, user_id)
        if not user:
            logger.warning("User not found for password change: %s", user_id)
            return False

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            logger.warning("Password change failed: incorrect current password for user %s", user_id)
            return False

        # Hash new password
        password_hash = get_password_hash(new_password)

        # Update password
        user.password_hash = password_hash
        await db.flush()

        logger.info("Password changed successfully for user: %s", user_id)

        return True

    # Helper methods

    async def get_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """
        Get a user by internal ID.

        Args:
            db: Database session
            user_id: Internal user UUID

        Returns:
            User instance or None if not found
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """
        Get a user by email.

        Args:
            db: Database session
            email: User email address

        Returns:
            User instance or None if not found
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        db: AsyncSession,
        phone_number: str,
    ) -> Optional[User]:
        """
        Get a user by phone number.

        Args:
            db: Database session
            phone_number: User phone number

        Returns:
            User instance or None if not found
        """
        result = await db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def _create_guest_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        preferred_language: str = "en",
    ) -> GuestProfile:
        """
        Internal method to create a guest profile for a user.

        Args:
            db: Database session
            user_id: User UUID
            preferred_language: Preferred language code

        Returns:
            Created GuestProfile instance
        """
        guest_profile = GuestProfile(
            user_id=user_id,
            preferred_language=preferred_language,
        )

        db.add(guest_profile)
        await db.flush()
        await db.refresh(guest_profile)

        return guest_profile


# Global service instance
auth_service = AuthService()
