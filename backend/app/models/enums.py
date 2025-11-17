"""
Database enum types for BOMA application.
"""
import enum


class UserStatus(str, enum.Enum):
    """User account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class BusinessType(str, enum.Enum):
    """Host business type."""
    INDIVIDUAL = "individual"
    BUSINESS = "business"


class VerificationStatus(str, enum.Enum):
    """Verification status for hosts and properties."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class KYCDocumentType(str, enum.Enum):
    """Types of KYC documents."""
    NIDA = "nida"
    PASSPORT = "passport"
    BUSINESS_REG = "business_reg"
    TAX_CERT = "tax_cert"
    UTILITY_BILL = "utility_bill"


class DocumentStatus(str, enum.Enum):
    """Status of uploaded documents."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PropertyType(str, enum.Enum):
    """Types of rental properties."""
    APARTMENT = "apartment"
    HOUSE = "house"
    ROOM = "room"
    STUDIO = "studio"
    VILLA = "villa"


class PropertyStatus(str, enum.Enum):
    """Property listing status."""
    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


class AmenityCategory(str, enum.Enum):
    """Categories of property amenities."""
    BASIC = "basic"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    ENTERTAINMENT = "entertainment"
    SAFETY = "safety"
    OUTDOOR = "outdoor"


class CancellationPolicy(str, enum.Enum):
    """Booking cancellation policies."""
    FLEXIBLE = "flexible"
    MODERATE = "moderate"
    STRICT = "strict"


class BookingStatus(str, enum.Enum):
    """Status of bookings."""
    PENDING = "pending"
    AWAITING_PAYMENT = "awaiting_payment"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatusEnum(str, enum.Enum):
    """Payment status for bookings."""
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"


class PaymentGateway(str, enum.Enum):
    """Payment gateway providers."""
    AZAMPAY = "azampay"
    SELCOM = "selcom"
    STRIPE = "stripe"


class PaymentMethod(str, enum.Enum):
    """Payment methods."""
    MOBILE_MONEY = "mobile_money"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class TransactionStatus(str, enum.Enum):
    """Payment transaction status."""
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PayoutStatus(str, enum.Enum):
    """Payout status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PayoutMethod(str, enum.Enum):
    """Payout methods to hosts."""
    MOBILE_MONEY = "mobile_money"
    BANK_TRANSFER = "bank_transfer"


class RefundReason(str, enum.Enum):
    """Reasons for refunds."""
    CANCELLATION = "cancellation"
    DISPUTE = "dispute"
    DAMAGE_WAIVER = "damage_waiver"
    SYSTEM_ERROR = "system_error"


class AccountType(str, enum.Enum):
    """Account types for double-entry ledger."""
    GUEST_WALLET = "guest_wallet"
    HOST_WALLET = "host_wallet"
    PLATFORM_WALLET = "platform_wallet"
    GATEWAY_RECEIVABLE = "gateway_receivable"
    PLATFORM_REVENUE = "platform_revenue"
    GATEWAY_FEES = "gateway_fees"


class ReferenceType(str, enum.Enum):
    """Reference types for ledger transactions."""
    PAYMENT = "payment"
    PAYOUT = "payout"
    REFUND = "refund"
    BOOKING = "booking"
    FEE = "fee"


class PricingRuleType(str, enum.Enum):
    """Types of pricing rules."""
    WEEKLY_DISCOUNT = "weekly_discount"
    MONTHLY_DISCOUNT = "monthly_discount"
    WEEKEND_PREMIUM = "weekend_premium"
    SEASONAL = "seasonal"


class TicketCategory(str, enum.Enum):
    """Support ticket categories."""
    BOOKING_ISSUE = "booking_issue"
    PAYMENT_ISSUE = "payment_issue"
    PROPERTY_ISSUE = "property_issue"
    ACCOUNT_ISSUE = "account_issue"
    OTHER = "other"


class PriorityLevel(str, enum.Enum):
    """Priority levels for tickets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, enum.Enum):
    """Support ticket status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    WAITING_ADMIN = "waiting_admin"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputeType(str, enum.Enum):
    """Types of disputes."""
    DAMAGE_CLAIM = "damage_claim"
    REFUND_REQUEST = "refund_request"
    CANCELLATION_DISPUTE = "cancellation_dispute"
    OTHER = "other"


class DisputeStatus(str, enum.Enum):
    """Dispute status."""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    CLOSED = "closed"


class DisputeResolution(str, enum.Enum):
    """Dispute resolution outcomes."""
    APPROVED = "approved"
    PARTIAL = "partial"
    DENIED = "denied"


class NotificationType(str, enum.Enum):
    """Notification delivery types."""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


class NotificationChannel(str, enum.Enum):
    """Notification channels/categories."""
    BOOKING = "booking"
    PAYMENT = "payment"
    MESSAGE = "message"
    REVIEW = "review"
    MARKETING = "marketing"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"
