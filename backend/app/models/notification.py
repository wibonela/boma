"""
Notification and system event models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)


class Notification(BaseModel):
    """User notifications (push, SMS, email)."""

    __tablename__ = "notifications"

    # Related entities
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Notification details
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel"),
        nullable=False
    )

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSONB)  # Additional payload for deep linking, etc.

    # Status
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True
    )

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, status={self.status})>"


class SystemEvent(BaseModel):
    """Event log for business events (for analytics and automation)."""

    __tablename__ = "system_events"

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # User who triggered the event (optional)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True
    )

    # Event data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        Index("idx_system_events_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<SystemEvent(id={self.id}, type={self.event_type}, entity={self.entity_type})>"
