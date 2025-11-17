"""
User profile endpoints.

Handles user, guest profile, and host profile management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, require_host_role
from app.core.logging_config import get_logger
from app.db.session import get_db

logger = get_logger(__name__)
from app.models.user import User
from app.schemas.user import (
    GuestProfileResponse,
    GuestProfileUpdate,
    HostProfileCreate,
    HostProfileResponse,
    HostProfileUpdate,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import user_service


router = APIRouter(prefix="/users", tags=["users"])


# ============================================================================
# User Endpoints
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get the current authenticated user's profile.

    Returns basic user information including roles and verification status.
    """
    logger.info("User %s requested their profile", current_user.id)
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update the current user's basic information.

    Only allows updating email, phone_number, and country_code.
    """
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    updated_user = await user_service.update_user(
        db=db,
        user_id=current_user.id,
        **update_data
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.commit()

    logger.info("User %s updated their profile", current_user.id)
    return UserResponse.model_validate(updated_user)


@router.get("/me/complete", response_model=UserProfileResponse)
async def get_complete_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Get the complete user profile including guest and host profiles.

    Returns user data along with guest_profile and host_profile if they exist.
    """
    # Load user with profiles
    user = await user_service.get_by_id(
        db=db,
        user_id=current_user.id,
        load_profiles=True
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    guest_profile_response = None
    if user.guest_profile:
        guest_profile_response = GuestProfileResponse.model_validate(user.guest_profile)

    host_profile_response = None
    if user.host_profile:
        host_profile_response = HostProfileResponse.model_validate(user.host_profile)

    return UserProfileResponse(
        user=UserResponse.model_validate(user),
        guest_profile=guest_profile_response,
        host_profile=host_profile_response,
    )


# ============================================================================
# Guest Profile Endpoints
# ============================================================================

@router.get("/guest-profile", response_model=GuestProfileResponse)
async def get_guest_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuestProfileResponse:
    """
    Get the current user's guest profile.

    Returns 404 if the user doesn't have a guest profile.
    """
    user = await user_service.get_by_id(
        db=db,
        user_id=current_user.id,
        load_profiles=True
    )

    if not user or not user.guest_profile:
        # Auto-create guest profile if it doesn't exist
        if user:
            guest_profile = await user_service.create_guest_profile(
                db=db,
                user_id=user.id
            )
            await db.commit()
            logger.info("Auto-created guest profile for user %s", user.id)
            return GuestProfileResponse.model_validate(guest_profile)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest profile not found"
        )

    return GuestProfileResponse.model_validate(user.guest_profile)


@router.put("/guest-profile", response_model=GuestProfileResponse)
async def update_guest_profile(
    profile_update: GuestProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuestProfileResponse:
    """
    Update the current user's guest profile.

    Creates the guest profile if it doesn't exist.
    """
    update_data = profile_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Try to update existing profile
    updated_profile = await user_service.update_guest_profile(
        db=db,
        user_id=current_user.id,
        **update_data
    )

    # If profile doesn't exist, create it
    if not updated_profile:
        guest_profile = await user_service.create_guest_profile(
            db=db,
            user_id=current_user.id,
            **update_data
        )
        await db.commit()
        logger.info("Created guest profile for user %s", current_user.id)
        return GuestProfileResponse.model_validate(guest_profile)

    await db.commit()

    logger.info("User %s updated their guest profile", current_user.id)
    return GuestProfileResponse.model_validate(updated_profile)


# ============================================================================
# Host Profile Endpoints
# ============================================================================

@router.post("/host-profile", response_model=HostProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_host_profile(
    profile_data: HostProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HostProfileResponse:
    """
    Create a host profile for the current user.

    This endpoint enables the user to become a host. Returns 400 if
    the user already has a host profile.
    """
    # Check if user already has a host profile
    user = await user_service.get_by_id(
        db=db,
        user_id=current_user.id,
        load_profiles=True
    )

    if user and user.host_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a host profile"
        )

    # Create host profile
    profile_dict = profile_data.model_dump()
    business_type = profile_dict.pop("business_type")

    host_profile = await user_service.create_host_profile(
        db=db,
        user_id=current_user.id,
        business_type=business_type,
        **profile_dict
    )

    await db.commit()

    logger.info("User %s created host profile", current_user.id)
    return HostProfileResponse.model_validate(host_profile)


@router.get("/host-profile", response_model=HostProfileResponse)
async def get_host_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HostProfileResponse:
    """
    Get the current user's host profile.

    Returns 404 if the user doesn't have a host profile.
    """
    user = await user_service.get_by_id(
        db=db,
        user_id=current_user.id,
        load_profiles=True
    )

    if not user or not user.host_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found. Create one with POST /users/host-profile"
        )

    return HostProfileResponse.model_validate(user.host_profile)


@router.put("/host-profile", response_model=HostProfileResponse)
async def update_host_profile(
    profile_update: HostProfileUpdate,
    current_user: User = Depends(require_host_role),
    db: AsyncSession = Depends(get_db),
) -> HostProfileResponse:
    """
    Update the current user's host profile.

    Requires that the user has a host role. Returns 404 if host profile doesn't exist.
    """
    update_data = profile_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    updated_profile = await user_service.update_host_profile(
        db=db,
        user_id=current_user.id,
        **update_data
    )

    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host profile not found"
        )

    await db.commit()

    logger.info("User %s updated their host profile", current_user.id)
    return HostProfileResponse.model_validate(updated_profile)
