"""
Import all models for Alembic auto-detection.
"""
from app.models.base import BaseModel
from app.models.enums import *
from app.models.user import User, GuestProfile, HostProfile, KYCDocument
from app.models.property import Property, PropertyPhoto, Amenity, PropertyAmenity
from app.models.availability import AvailabilityRule, AvailabilityOverride
from app.models.pricing import PricingRule
from app.models.booking import Booking, Review
from app.models.payment import Payment, Payout, Refund, Transaction
from app.models.support import SupportTicket, Dispute
from app.models.notification import Notification, SystemEvent

__all__ = [
    "BaseModel",
    # User models
    "User",
    "GuestProfile",
    "HostProfile",
    "KYCDocument",
    # Property models
    "Property",
    "PropertyPhoto",
    "Amenity",
    "PropertyAmenity",
    # Availability models
    "AvailabilityRule",
    "AvailabilityOverride",
    # Pricing models
    "PricingRule",
    # Booking models
    "Booking",
    "Review",
    # Payment models
    "Payment",
    "Payout",
    "Refund",
    "Transaction",
    # Support models
    "SupportTicket",
    "Dispute",
    # Notification models
    "Notification",
    "SystemEvent",
]
