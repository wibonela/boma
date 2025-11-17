"""
Property-related models.
"""
from datetime import datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, Base
from app.models.enums import (
    AmenityCategory,
    CancellationPolicy,
    PropertyStatus,
    PropertyType,
    VerificationStatus,
)


class Property(BaseModel):
    """Rentable properties listed by hosts."""

    __tablename__ = "properties"

    # Owner
    host_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Basic information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType, name="property_type"),
        nullable=False,
        index=True
    )

    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="TZ")

    # Geolocation
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(11, 8), nullable=False)

    # Property details
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    square_meters: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))

    # Pricing
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TZS")
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Booking rules
    minimum_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    maximum_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=365)
    check_in_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(14, 0))
    check_out_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(11, 0))
    cancellation_policy: Mapped[CancellationPolicy] = mapped_column(
        Enum(CancellationPolicy, name="cancellation_policy"),
        default=CancellationPolicy.MODERATE,
        nullable=False
    )

    # House rules
    pets_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    smoking_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parties_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    children_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    house_rules: Mapped[Optional[str]] = mapped_column(Text)

    # Status and verification
    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, name="property_status"),
        default=PropertyStatus.DRAFT,
        nullable=False,
        index=True
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNVERIFIED,
        nullable=False
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Features
    instant_book: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    photos: Mapped[list["PropertyPhoto"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan",
        order_by="PropertyPhoto.display_order"
    )
    property_amenities: Mapped[list["PropertyAmenity"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )
    availability_rules: Mapped[list["AvailabilityRule"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )
    availability_overrides: Mapped[list["AvailabilityOverride"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )
    pricing_rules: Mapped[list["PricingRule"]] = relationship(
        back_populates="property",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_property_location", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Property(id={self.id}, title={self.title})>"


class PropertyPhoto(BaseModel):
    """Photos of properties."""

    __tablename__ = "property_photos"

    # Foreign key
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Photo URLs
    photo_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Display settings
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(String(500))

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_by: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationship
    property: Mapped["Property"] = relationship(back_populates="photos")

    __table_args__ = (
        Index("idx_property_photo_order", "property_id", "display_order"),
    )

    def __repr__(self) -> str:
        return f"<PropertyPhoto(id={self.id}, property_id={self.property_id})>"


class Amenity(BaseModel):
    """Master list of available amenities."""

    __tablename__ = "amenities"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[AmenityCategory] = mapped_column(
        Enum(AmenityCategory, name="amenity_category"),
        nullable=False
    )
    icon: Mapped[Optional[str]] = mapped_column(String(50))

    # Relationship
    property_amenities: Mapped[list["PropertyAmenity"]] = relationship(
        back_populates="amenity",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Amenity(id={self.id}, name={self.name})>"


class PropertyAmenity(Base):
    """Join table for property amenities."""

    __tablename__ = "property_amenities"

    # Composite primary key
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )
    amenity_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("amenities.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="property_amenities")
    amenity: Mapped["Amenity"] = relationship(back_populates="property_amenities")

    __table_args__ = (
        Index("idx_property_amenities_property", "property_id"),
        Index("idx_property_amenities_amenity", "amenity_id"),
        UniqueConstraint("property_id", "amenity_id", name="uq_property_amenity"),
    )

    def __repr__(self) -> str:
        return f"<PropertyAmenity(property_id={self.property_id}, amenity_id={self.amenity_id})>"


# Import here to avoid circular imports
from app.models.availability import AvailabilityRule, AvailabilityOverride
from app.models.pricing import PricingRule
