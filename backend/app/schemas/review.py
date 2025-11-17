"""
Pydantic schemas for review-related requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ReviewBase(BaseModel):
    """Base review schema with common fields."""
    rating: int = Field(..., ge=1, le=5, description="Overall rating (1-5)")
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    location_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=5000)


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""
    booking_id: UUID
    is_public: bool = True


class ReviewUpdate(BaseModel):
    """Schema for updating a review (partial update)."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    location_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=5000)
    is_public: Optional[bool] = None


class HostResponseCreate(BaseModel):
    """Schema for host responding to a review."""
    host_response: str = Field(..., max_length=2000)


class ReviewResponse(ReviewBase):
    """Review response schema."""
    id: UUID
    booking_id: UUID
    property_id: UUID
    host_id: UUID
    guest_id: UUID
    is_public: bool
    host_response: Optional[str] = None
    host_responded_at: Optional[datetime] = None
    flagged: bool
    flagged_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewWithGuestInfo(ReviewResponse):
    """Review response with guest information."""
    guest_name: Optional[str] = None
    guest_photo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PropertyRatingSummary(BaseModel):
    """Summary of property ratings."""
    property_id: UUID
    total_reviews: int
    average_rating: float
    average_cleanliness: Optional[float] = None
    average_accuracy: Optional[float] = None
    average_communication: Optional[float] = None
    average_location: Optional[float] = None
    average_value: Optional[float] = None
    rating_distribution: dict[int, int] = Field(
        default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    )

    model_config = ConfigDict(from_attributes=True)
