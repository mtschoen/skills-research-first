"""orderflow: a small order-processing and reporting library."""

__version__ = "0.1.0"

from .core import Order, proc
from .orders import handle_order_input
from .report import daily_total, grand_summary

__all__ = [
    "Order",
    "proc",
    "handle_order_input",
    "daily_total",
    "grand_summary",
]
