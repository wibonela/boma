"""
Pydantic schemas for user-related requests and responses.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    phone_number: Optional[str] = None
    country_code: str = Field(default="TZ", max_length=2)


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    clerk_id: str
    is_guest: bool
    is_host: bool
    is_admin: bool
    status: str
    email_verified: bool
    phone_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """User update schema (partial)."""
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    country_code: Optional[str] = Field(None, max_length=2)


# ============================================================================
# Guest Profile Schemas
# ============================================================================

class GuestProfileBase(BaseModel):
    """Base guest profile schema."""
    preferred_language: str = Field(default="en", max_length=10)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)
    government_id_type: Optional[str] = Field(None, max_length=50)
    government_id_number: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    profile_photo_url: Optional[str] = None


class GuestProfileCreate(GuestProfileBase):
    """Schema for creating a guest profile."""
    pass


class GuestProfileUpdate(BaseModel):
    """Schema for updating a guest profile (partial)."""
    preferred_language: Optional[str] = Field(None, max_length=10)
    emergency_contact_name: Optional[str] = Field(None, max_length=255)
    emergency_contact_phone: Optional[str] = Field(None, max_length=50)
    government_id_type: Optional[str] = Field(None, max_length=50)
    government_id_number: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    profile_photo_url: Optional[str] = None


class GuestProfileResponse(GuestProfileBase):
    """Guest profile response schema."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Host Profile Schemas
# ============================================================================

class HostProfileBase(BaseModel):
    """Base host profile schema."""
    business_type: str
    business_name: Optional[str] = Field(None, max_length=255)
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    payout_method: str = "mobile_money"
    payout_phone_number: Optional[str] = Field(None, max_length=50)
    payout_bank_name: Optional[str] = Field(None, max_length=100)
    payout_account_number: Optional[str] = Field(None, max_length=100)
    payout_account_name: Optional[str] = Field(None, max_length=255)
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None


class HostProfileCreate(HostProfileBase):
    """Schema for creating a host profile."""
    pass


class HostProfileUpdate(BaseModel):
    """Schema for updating a host profile (partial)."""
    business_type: Optional[str] = None
    business_name: Optional[str] = Field(None, max_length=255)
    business_registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    payout_method: Optional[str] = None
    payout_phone_number: Optional[str] = Field(None, max_length=50)
    payout_bank_name: Optional[str] = Field(None, max_length=100)
    payout_account_number: Optional[str] = Field(None, max_length=100)
    payout_account_name: Optional[str] = Field(None, max_length=255)
    profile_photo_url: Optional[str] = None
    bio: Optional[str] = None


class HostProfileResponse(HostProfileBase):
    """Host profile response schema."""
    id: UUID
    user_id: UUID
    verification_status: str
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    response_rate: float
    response_time_hours: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Combined User Profile Schemas
# ============================================================================

class UserProfileResponse(BaseModel):
    """Complete user profile including user, guest, and host profiles."""
    user: UserResponse
    guest_profile: Optional[GuestProfileResponse] = None
    host_profile: Optional[HostProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
