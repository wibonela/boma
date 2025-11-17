"""
Payment and financial transaction models.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import (
    AccountType,
    PaymentGateway,
    PaymentMethod,
    PayoutMethod,
    PayoutStatus,
    ReferenceType,
    RefundReason,
    TransactionStatus,
)


class Payment(BaseModel):
    """Incoming payments from guests."""

    __tablename__ = "payments"

    # Related entities
    booking_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    guest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Gateway details
    gateway: Mapped[PaymentGateway] = mapped_column(
        Enum(PaymentGateway, name="payment_gateway"),
        nullable=False
    )
    gateway_reference: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method"),
        nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(50))

    # Status
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        default=TransactionStatus.INITIATED,
        nullable=False,
        index=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Fees
    gateway_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Timestamps
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status})>"


class Payout(BaseModel):
    """Outgoing payments to hosts."""

    __tablename__ = "payouts"

    # Related entities
    host_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Payout method
    payout_method: Mapped[PayoutMethod] = mapped_column(
        Enum(PayoutMethod, name="payout_method"),
        nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(50))
    bank_name: Mapped[Optional[str]] = mapped_column(String(100))
    account_number: Mapped[Optional[str]] = mapped_column(String(100))
    account_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Gateway details
    gateway: Mapped[Optional[PaymentGateway]] = mapped_column(
        Enum(PaymentGateway, name="payment_gateway")
    )
    gateway_reference: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)

    # Status
    status: Mapped[PayoutStatus] = mapped_column(
        Enum(PayoutStatus, name="payout_status"),
        default=PayoutStatus.PENDING,
        nullable=False,
        index=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Fees
    gateway_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Payout(id={self.id}, host_id={self.host_id}, amount={self.amount}, status={self.status})>"


class Refund(BaseModel):
    """Refunds issued to guests."""

    __tablename__ = "refunds"

    # Related entities
    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    booking_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    guest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Reason
    reason: Mapped[RefundReason] = mapped_column(
        Enum(RefundReason, name="refund_reason"),
        nullable=False
    )
    reason_detail: Mapped[Optional[str]] = mapped_column(Text)

    # Gateway details
    gateway: Mapped[PaymentGateway] = mapped_column(
        Enum(PaymentGateway, name="payment_gateway"),
        nullable=False
    )
    gateway_reference: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)

    # Status
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status"),
        default=TransactionStatus.PENDING,
        nullable=False,
        index=True
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Processing
    processed_by: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Refund(id={self.id}, amount={self.amount}, status={self.status})>"


class Transaction(BaseModel):
    """Double-entry ledger for all financial movements."""

    __tablename__ = "transactions"

    # Transaction grouping
    transaction_group_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Account details
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type"),
        nullable=False
    )
    entity_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True), index=True)

    # Debit/Credit
    debit: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Reference
    reference_type: Mapped[ReferenceType] = mapped_column(
        Enum(ReferenceType, name="reference_type"),
        nullable=False
    )
    reference_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Description
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    __table_args__ = (
        Index("idx_transactions_group", "transaction_group_id"),
        Index("idx_transactions_entity", "entity_id"),
        Index("idx_transactions_reference", "reference_type", "reference_id"),
    )

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.account_type}, debit={self.debit}, credit={self.credit})>"
