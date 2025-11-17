"""
Booking and review-related models.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import (
    BookingStatus,
    CancellationPolicy,
    PaymentStatusEnum,
)


class Booking(BaseModel):
    """Core booking records."""

    __tablename__ = "bookings"

    # Related entities
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    guest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    host_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Dates
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    num_nights: Mapped[int] = mapped_column(Integer, nullable=False)
    num_guests: Mapped[int] = mapped_column(Integer, nullable=False)

    # Pricing (captured at booking time)
    base_price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_nights_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cleaning_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Status
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_status: Mapped[PaymentStatusEnum] = mapped_column(
        Enum(PaymentStatusEnum, name="payment_status_enum"),
        default=PaymentStatusEnum.UNPAID,
        nullable=False
    )

    # Cancellation
    cancellation_policy: Mapped[CancellationPolicy] = mapped_column(
        Enum(CancellationPolicy, name="cancellation_policy"),
        nullable=False
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Guest requests
    special_requests: Mapped[Optional[str]] = mapped_column(Text)
    check_in_instructions: Mapped[Optional[str]] = mapped_column(Text)

    # Check-in/out confirmation
    check_in_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    check_out_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Expiry for pending bookings
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    review: Mapped[Optional["Review"]] = relationship(
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_bookings_dates", "check_in_date", "check_out_date"),
    )

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, status={self.status})>"


class Review(BaseModel):
    """Reviews from guests about properties and hosts."""

    __tablename__ = "reviews"

    # Foreign keys
    booking_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    host_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    guest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Overall rating (1-5)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    # Category ratings (1-5)
    cleanliness_rating: Mapped[Optional[int]] = mapped_column(Integer)
    accuracy_rating: Mapped[Optional[int]] = mapped_column(Integer)
    communication_rating: Mapped[Optional[int]] = mapped_column(Integer)
    location_rating: Mapped[Optional[int]] = mapped_column(Integer)
    value_rating: Mapped[Optional[int]] = mapped_column(Integer)

    # Review content
    comment: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Host response
    host_response: Mapped[Optional[str]] = mapped_column(Text)
    host_responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Moderation
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    flagged_reason: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationship
    booking: Mapped["Booking"] = relationship(back_populates="review")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        CheckConstraint(
            "cleanliness_rating IS NULL OR (cleanliness_rating >= 1 AND cleanliness_rating <= 5)",
            name="check_cleanliness_rating_range"
        ),
        CheckConstraint(
            "accuracy_rating IS NULL OR (accuracy_rating >= 1 AND accuracy_rating <= 5)",
            name="check_accuracy_rating_range"
        ),
        CheckConstraint(
            "communication_rating IS NULL OR (communication_rating >= 1 AND communication_rating <= 5)",
            name="check_communication_rating_range"
        ),
        CheckConstraint(
            "location_rating IS NULL OR (location_rating >= 1 AND location_rating <= 5)",
            name="check_location_rating_range"
        ),
        CheckConstraint(
            "value_rating IS NULL OR (value_rating >= 1 AND value_rating <= 5)",
            name="check_value_rating_range"
        ),
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, booking_id={self.booking_id}, rating={self.rating})>"
