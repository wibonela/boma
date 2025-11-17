"""
Support and dispute models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import (
    DisputeResolution,
    DisputeStatus,
    DisputeType,
    PriorityLevel,
    TicketCategory,
    TicketStatus,
)


class SupportTicket(BaseModel):
    """Customer support tickets."""

    __tablename__ = "support_tickets"

    # Related entities
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL")
    )
    property_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="SET NULL")
    )

    # Ticket details
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory, name="ticket_category"),
        nullable=False
    )
    priority: Mapped[PriorityLevel] = mapped_column(
        Enum(PriorityLevel, name="priority_level"),
        default=PriorityLevel.MEDIUM,
        nullable=False
    )
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.OPEN,
        nullable=False,
        index=True
    )

    # Content
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Assignment
    assigned_to: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True
    )

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, status={self.status}, category={self.category})>"


class Dispute(BaseModel):
    """Damage and refund disputes."""

    __tablename__ = "disputes"

    # Related entities
    booking_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    claimant_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    respondent_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Dispute details
    dispute_type: Mapped[DisputeType] = mapped_column(
        Enum(DisputeType, name="dispute_type"),
        nullable=False
    )
    claim_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Description and evidence
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[Optional[dict]] = mapped_column(JSONB)  # Array of photo URLs

    # Status and resolution
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus, name="dispute_status"),
        default=DisputeStatus.OPEN,
        nullable=False,
        index=True
    )
    resolution: Mapped[Optional[DisputeResolution]] = mapped_column(
        Enum(DisputeResolution, name="dispute_resolution")
    )
    resolution_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Admin handling
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Dispute(id={self.id}, type={self.dispute_type}, status={self.status})>"
