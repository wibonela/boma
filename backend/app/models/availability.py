"""
Availability-related models for properties.
"""
from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AvailabilityRule(BaseModel):
    """Default availability rules for properties."""

    __tablename__ = "availability_rules"

    # Foreign key
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Day of week (0-6, Sunday-Saturday), NULL for all days
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)

    # Overrides for minimum/maximum nights
    min_nights: Mapped[Optional[int]] = mapped_column(Integer)
    max_nights: Mapped[Optional[int]] = mapped_column(Integer)

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    property: Mapped["Property"] = relationship(back_populates="availability_rules")

    def __repr__(self) -> str:
        return f"<AvailabilityRule(property_id={self.property_id}, day={self.day_of_week})>"


class AvailabilityOverride(BaseModel):
    """Specific date overrides for availability."""

    __tablename__ = "availability_overrides"

    # Foreign key
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False
    )

    # Specific date
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship
    property: Mapped["Property"] = relationship(back_populates="availability_overrides")

    __table_args__ = (
        UniqueConstraint("property_id", "date", name="uq_property_date"),
        Index("idx_availability_overrides_property_date", "property_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<AvailabilityOverride(property_id={self.property_id}, date={self.date})>"
