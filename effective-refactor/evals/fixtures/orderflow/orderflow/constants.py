"""Shared configuration constants for the orderflow package."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PricingRules:
    """Typed pricing rules used to compute order totals."""

    tax_rate: float
    shipping_flat: float
    express_multiplier: float
    discount_threshold: float
    discount_rate: float


PRICING = PricingRules(
    tax_rate=0.08,
    shipping_flat=5.0,
    express_multiplier=2.5,
    discount_threshold=100.0,
    discount_rate=0.1,
)

LOW_STOCK_THRESHOLD = 5

CUSTOMER_ID_PREFIX = "CUST-"
