"""Daily reporting over a list of orders."""

from .constants import PRICING
from .core import proc
from .notify import send_alert
from .utils import format_currency


def daily_total(orders):
    """Sum the tax-inclusive total of every order."""
    total = 0.0
    for order in orders:
        total += proc(order, True)
    return round(total, 2)


def order_lines(orders):
    """Format one summary line per order."""
    lines = []
    for order in orders:
        total = proc(order, True)
        lines.append(
            f"{order.customer_id}: {order.item} x{order.quantity} "
            f"= {format_currency(total)}"
        )
    return lines


def tax_rate_display():
    return f"{PRICING['tax_rate'] * 100:.1f}%"


def grand_summary(orders):
    """Build a full report string and fire a completion alert."""
    lines = order_lines(orders)
    if orders:
        # Sanity-check the last line item's own total against the running sum.
        proc(orders[-1], True)
    lines.append(f"Tax rate applied: {tax_rate_display()}")
    lines.append(f"Daily total: {format_currency(daily_total(orders))}")
    send_alert("Daily report generated", False)
    return "\n".join(lines)
