"""
Pricing-related models for properties.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Index, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import PricingRuleType


class PricingRule(BaseModel):
    """Dynamic pricing rules for properties."""

    __tablename__ = "pricing_rules"

    # Foreign key
    property_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Rule type
    rule_type: Mapped[PricingRuleType] = mapped_column(
        Enum(PricingRuleType, name="pricing_rule_type"),
        nullable=False
    )

    # Discount/premium percentage (negative for premium)
    discount_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # Date range for seasonal rules
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    # Minimum nights for discount to apply
    min_nights: Mapped[Optional[int]] = mapped_column(Integer)

    # Active flag
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationship
    property: Mapped["Property"] = relationship(back_populates="pricing_rules")

    __table_args__ = (
        Index("idx_pricing_rules_property", "property_id"),
        Index("idx_pricing_rules_dates", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        return f"<PricingRule(id={self.id}, type={self.rule_type})>"
