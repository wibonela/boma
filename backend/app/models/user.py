"""
User and authentication related models.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import (
    BusinessType,
    DocumentStatus,
    KYCDocumentType,
    PayoutMethod,
    UserStatus,
    VerificationStatus,
)


class User(BaseModel):
    """Core user model for all platform users."""

    __tablename__ = "users"

    # Authentication
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(500))
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Location
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="TZ")

    # Roles
    is_guest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_host: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        default=UserStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Verification
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    guest_profile: Mapped[Optional["GuestProfile"]] = relationship(
        back_populates="user",
        foreign_keys="[GuestProfile.user_id]",
        uselist=False,
        cascade="all, delete-orphan"
    )
    host_profile: Mapped[Optional["HostProfile"]] = relationship(
        back_populates="user",
        foreign_keys="[HostProfile.user_id]",
        uselist=False,
        cascade="all, delete-orphan"
    )
    kyc_documents: Mapped[list["KYCDocument"]] = relationship(
        back_populates="user",
        foreign_keys="[KYCDocument.user_id]",
        cascade="all, delete-orphan"
    )

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class GuestProfile(BaseModel):
    """Extended profile for users acting as guests."""

    __tablename__ = "guest_profiles"

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Preferences
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    # Emergency contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(50))

    # Government ID (encrypted in production)
    government_id_type: Mapped[Optional[str]] = mapped_column(String(50))
    government_id_number: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)

    # Profile photo
    profile_photo_url: Mapped[Optional[str]] = mapped_column(Text)

    # Relationship
    user: Mapped["User"] = relationship(
        back_populates="guest_profile",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<GuestProfile(user_id={self.user_id})>"


class HostProfile(BaseModel):
    """Extended profile for users acting as hosts."""

    __tablename__ = "host_profiles"

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Business information
    business_type: Mapped[BusinessType] = mapped_column(
        Enum(BusinessType, name="business_type"),
        nullable=False
    )
    business_name: Mapped[Optional[str]] = mapped_column(String(255))
    business_registration_number: Mapped[Optional[str]] = mapped_column(String(100))
    tax_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Payout information
    payout_method: Mapped[PayoutMethod] = mapped_column(
        Enum(PayoutMethod, name="payout_method"),
        default=PayoutMethod.MOBILE_MONEY,
        nullable=False
    )
    payout_phone_number: Mapped[Optional[str]] = mapped_column(String(50))
    payout_bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    payout_account_number: Mapped[Optional[str]] = mapped_column(String(100))
    payout_account_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Verification
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.UNVERIFIED,
        nullable=False,
        index=True
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Profile
    profile_photo_url: Mapped[Optional[str]] = mapped_column(Text)
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Performance metrics
    response_rate: Mapped[float] = mapped_column(default=0.00, nullable=False)
    response_time_hours: Mapped[Optional[int]]

    # Relationship
    user: Mapped["User"] = relationship(
        back_populates="host_profile",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<HostProfile(user_id={self.user_id}, verification={self.verification_status})>"


class KYCDocument(BaseModel):
    """KYC documents uploaded by users."""

    __tablename__ = "kyc_documents"

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Document details
    document_type: Mapped[KYCDocumentType] = mapped_column(
        Enum(KYCDocumentType, name="kyc_document_type"),
        nullable=False
    )
    document_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Review status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Review metadata
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Document expiry
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    # Relationship
    user: Mapped["User"] = relationship(
        back_populates="kyc_documents",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<KYCDocument(id={self.id}, type={self.document_type}, status={self.status})>"
