"""
Property-related Pydantic schemas.
"""
from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import (
    PropertyType,
    PropertyStatus,
    VerificationStatus,
    CancellationPolicy,
)


# Property Schemas
class PropertyBase(BaseModel):
    """Base property schema with common fields."""
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=20)
    property_type: PropertyType
    address_line1: str = Field(..., min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country_code: str = Field(default="TZ", max_length=2)
    bedrooms: int = Field(..., ge=0, le=50)
    bathrooms: Decimal = Field(..., ge=0, le=50)
    max_guests: int = Field(..., ge=1, le=100)
    square_meters: Optional[Decimal] = Field(None, ge=0)
    base_price: Decimal = Field(..., gt=0, alias="base_price_per_night")
    currency: str = Field(default="TZS", max_length=3)
    cleaning_fee: Decimal = Field(default=Decimal("0.00"), ge=0)
    deposit_amount: Optional[Decimal] = Field(default=None, ge=0)
    minimum_nights: int = Field(default=1, ge=1, le=365)
    maximum_nights: int = Field(default=365, ge=1, le=3650)
    check_in_time: Optional[time] = Field(default=time(14, 0))
    check_out_time: Optional[time] = Field(default=time(11, 0))
    cancellation_policy: CancellationPolicy = Field(default=CancellationPolicy.MODERATE)
    pets_allowed: bool = Field(default=False)
    smoking_allowed: bool = Field(default=False)
    parties_allowed: bool = Field(default=False)
    children_allowed: bool = Field(default=True)
    house_rules: Optional[str] = None
    instant_book: bool = Field(default=False)


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""
    latitude: Optional[Decimal] = Field(default=Decimal("0.0"), ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=Decimal("0.0"), ge=-180, le=180)
    amenities: List[str] = Field(default_factory=list)


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property."""
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, min_length=20)
    property_type: Optional[PropertyType] = None
    address_line1: Optional[str] = Field(None, min_length=5, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country_code: Optional[str] = Field(None, max_length=2)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    bedrooms: Optional[int] = Field(None, ge=0, le=50)
    bathrooms: Optional[Decimal] = Field(None, ge=0, le=50)
    max_guests: Optional[int] = Field(None, ge=1, le=100)
    square_meters: Optional[Decimal] = Field(None, ge=0)
    base_price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    deposit_amount: Optional[Decimal] = Field(None, ge=0)
    minimum_nights: Optional[int] = Field(None, ge=1, le=365)
    maximum_nights: Optional[int] = Field(None, ge=1, le=3650)
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    cancellation_policy: Optional[CancellationPolicy] = None
    pets_allowed: Optional[bool] = None
    smoking_allowed: Optional[bool] = None
    parties_allowed: Optional[bool] = None
    children_allowed: Optional[bool] = None
    house_rules: Optional[str] = None
    instant_book: Optional[bool] = None
    active: Optional[bool] = None


class PropertyResponse(PropertyBase):
    """Schema for property responses."""
    id: UUID
    host_id: UUID
    latitude: Decimal
    longitude: Decimal
    region: str
    status: PropertyStatus
    verification_status: VerificationStatus
    verified_at: Optional[datetime] = None
    verified_by: Optional[UUID] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    amenities: List[str] = Field(default_factory=list)
    photos: List["PropertyPhotoResponse"] = Field(default_factory=list)

    # Rating fields (computed, not stored in database)
    average_rating: Optional[float] = None
    total_reviews: int = 0

    model_config = ConfigDict(from_attributes=True, use_enum_values=True, populate_by_name=True)


class PropertyList(BaseModel):
    """Schema for property list responses."""
    properties: List[PropertyResponse]
    total: int
    page: int
    page_size: int


# Property Search Schema
class PropertySearchParams(BaseModel):
    """Search and filter parameters for properties."""
    city: Optional[str] = None
    property_type: Optional[PropertyType] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[Decimal] = None
    max_guests: Optional[int] = None
    pets_allowed: Optional[bool] = None
    instant_book: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Property Photo Schemas
class PropertyPhotoBase(BaseModel):
    """Base property photo schema."""
    caption: Optional[str] = Field(None, max_length=500)
    display_order: int = Field(default=0, ge=0)
    is_cover: bool = Field(default=False)


class PropertyPhotoResponse(PropertyPhotoBase):
    """Schema for property photo responses."""
    id: UUID
    property_id: UUID
    photo_url: str
    thumbnail_url: str
    is_verified: bool
    uploaded_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyPhotoUpdate(BaseModel):
    """Schema for updating property photo metadata."""
    caption: Optional[str] = Field(None, max_length=500)
    display_order: Optional[int] = Field(None, ge=0)
    is_cover: Optional[bool] = None


class PropertyPhotoReorder(BaseModel):
    """Schema for reordering multiple photos."""
    photo_orders: List[dict] = Field(
        ...,
        description="List of {photo_id: UUID, display_order: int} objects"
    )

    # Example: [{"photo_id": "uuid-1", "display_order": 0}, {"photo_id": "uuid-2", "display_order": 1}]
