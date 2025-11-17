"""
User service layer.

Business logic for user management, including mapping Clerk IDs to internal users.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.user import User, GuestProfile, HostProfile

logger = get_logger(__name__)
from app.models.enums import UserStatus


class UserService:
    """Service for user-related business logic."""

    async def get_by_id(
        self,
        db: AsyncSession,
        user_id: UUID,
        load_profiles: bool = False
    ) -> Optional[User]:
        """
        Get a user by internal ID.

        Args:
            db: Database session
            user_id: Internal user UUID
            load_profiles: Whether to eagerly load guest and host profiles

        Returns:
            User instance or None if not found
        """
        query = select(User).where(User.id == user_id)

        if load_profiles:
            query = query.options(
                selectinload(User.guest_profile),
                selectinload(User.host_profile)
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_clerk_id(
        self,
        db: AsyncSession,
        clerk_id: str,
        load_profiles: bool = False
    ) -> Optional[User]:
        """
        Get a user by Clerk ID.

        Args:
            db: Database session
            clerk_id: External Clerk user ID
            load_profiles: Whether to eagerly load guest and host profiles

        Returns:
            User instance or None if not found
        """
        query = select(User).where(User.clerk_id == clerk_id)

        if load_profiles:
            query = query.options(
                selectinload(User.guest_profile),
                selectinload(User.host_profile)
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str
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

    async def create_user(
        self,
        db: AsyncSession,
        clerk_id: str,
        email: str,
        phone_number: Optional[str] = None,
        country_code: str = None,
        email_verified: bool = False,
        phone_verified: bool = False,
        is_guest: bool = True,
        is_host: bool = False,
        is_admin: bool = False,
    ) -> User:
        """
        Create a new user.

        Args:
            db: Database session
            clerk_id: External Clerk user ID
            email: User email address
            phone_number: User phone number (optional)
            country_code: ISO country code (defaults to settings.DEFAULT_COUNTRY)
            email_verified: Whether email is verified
            phone_verified: Whether phone is verified
            is_guest: Whether user has guest role
            is_host: Whether user has host role
            is_admin: Whether user is an admin

        Returns:
            Created User instance
        """
        if country_code is None:
            country_code = settings.DEFAULT_COUNTRY

        user = User(
            clerk_id=clerk_id,
            email=email,
            phone_number=phone_number,
            country_code=country_code,
            email_verified=email_verified,
            phone_verified=phone_verified,
            is_guest=is_guest,
            is_host=is_host,
            is_admin=is_admin,
            status=UserStatus.ACTIVE,
            last_login_at=datetime.utcnow(),
        )

        db.add(user)
        await db.flush()
        await db.refresh(user)

        logger.info("Created new user: %s (clerk_id=%s)", user.id, clerk_id)

        return user

    async def get_or_create_by_clerk_id(
        self,
        db: AsyncSession,
        clerk_user_id: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: bool = False,
        phone_verified: bool = False,
    ) -> User:
        """
        Get an existing user by Clerk ID, or create one if it doesn't exist.

        This is the main method used during authentication. When a user signs in
        for the first time, we create their user record. On subsequent logins,
        we retrieve the existing record and update last_login_at.

        Args:
            db: Database session
            clerk_user_id: External Clerk user ID
            email: User email (required for new users)
            phone_number: User phone number (optional)
            email_verified: Whether email is verified
            phone_verified: Whether phone is verified

        Returns:
            User instance (existing or newly created)

        Raises:
            ValueError: If user doesn't exist and email is not provided
        """
        # Try to get existing user
        user = await self.get_by_clerk_id(db, clerk_user_id, load_profiles=True)

        if user:
            # Update last login timestamp
            user.last_login_at = datetime.utcnow()
            await db.flush()
            logger.debug("Existing user logged in: %s", user.id)
            return user

        # User doesn't exist - create new one
        if not email:
            raise ValueError("Email is required to create a new user")

        user = await self.create_user(
            db=db,
            clerk_id=clerk_user_id,
            email=email,
            phone_number=phone_number,
            email_verified=email_verified,
            phone_verified=phone_verified,
            is_guest=True,  # All new users start as guests
            is_host=False,
            is_admin=False,
        )

        # Auto-create guest profile for new users
        await self.create_guest_profile(db, user.id)

        await db.commit()

        return user

    async def update_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        **updates
    ) -> Optional[User]:
        """
        Update user fields.

        Args:
            db: Database session
            user_id: User ID to update
            **updates: Fields to update

        Returns:
            Updated User instance or None if not found
        """
        user = await self.get_by_id(db, user_id)
        if not user:
            return None

        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await db.flush()
        await db.refresh(user)

        logger.info("Updated user %s: %s", user_id, list(updates.keys()))

        return user

    async def create_guest_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        preferred_language: str = "en"
    ) -> GuestProfile:
        """
        Create a guest profile for a user.

        Args:
            db: Database session
            user_id: User ID
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

        logger.info("Created guest profile for user: %s", user_id)

        return guest_profile

    async def create_host_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        business_type: str,
        **profile_data
    ) -> HostProfile:
        """
        Create a host profile for a user and enable host role.

        Args:
            db: Database session
            user_id: User ID
            business_type: Type of business (individual, company, etc.)
            **profile_data: Additional host profile fields

        Returns:
            Created HostProfile instance
        """
        from app.models.enums import BusinessType

        # Enable host role on user
        user = await self.get_by_id(db, user_id)
        if user:
            user.is_host = True
            await db.flush()

        host_profile = HostProfile(
            user_id=user_id,
            business_type=BusinessType(business_type),
            **profile_data
        )

        db.add(host_profile)
        await db.flush()
        await db.refresh(host_profile)

        logger.info("Created host profile for user: %s", user_id)

        return host_profile

    async def update_guest_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        **updates
    ) -> Optional[GuestProfile]:
        """
        Update guest profile fields.

        Args:
            db: Database session
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated GuestProfile instance or None if not found
        """
        result = await db.execute(
            select(GuestProfile).where(GuestProfile.user_id == user_id)
        )
        guest_profile = result.scalar_one_or_none()

        if not guest_profile:
            return None

        for key, value in updates.items():
            if hasattr(guest_profile, key):
                setattr(guest_profile, key, value)

        await db.flush()
        await db.refresh(guest_profile)

        logger.info("Updated guest profile for user %s", user_id)

        return guest_profile

    async def update_host_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
        **updates
    ) -> Optional[HostProfile]:
        """
        Update host profile fields.

        Args:
            db: Database session
            user_id: User ID
            **updates: Fields to update

        Returns:
            Updated HostProfile instance or None if not found
        """
        result = await db.execute(
            select(HostProfile).where(HostProfile.user_id == user_id)
        )
        host_profile = result.scalar_one_or_none()

        if not host_profile:
            return None

        for key, value in updates.items():
            if hasattr(host_profile, key):
                setattr(host_profile, key, value)

        await db.flush()
        await db.refresh(host_profile)

        logger.info("Updated host profile for user %s", user_id)

        return host_profile


# Global service instance
user_service = UserService()
