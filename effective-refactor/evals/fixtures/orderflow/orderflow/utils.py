"""Formatting and pricing-preview helpers."""

from .constants import PRICING
from .core import proc


def format_currency(amount):
    return f"${amount:.2f}"


def rounded_total(order, apply_tax):
    """Convenience wrapper returning a currency-formatted order total."""
    return format_currency(proc(order, apply_tax))


def discount_preview(subtotal):
    """Return the discount amount a given subtotal would receive."""
    if subtotal >= PRICING["discount_threshold"]:
        return round(subtotal * PRICING["discount_rate"], 2)
    return 0.0
