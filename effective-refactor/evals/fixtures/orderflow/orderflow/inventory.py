"""In-memory stock tracking and restock cost estimation."""

from .constants import LOW_STOCK_THRESHOLD
from .core import Order, price_order

STOCK = {
    "widget": 50,
    "gadget": 20,
    "gizmo": 8,
    "doohickey": 3,
}

RESTOCK_SUPPLIER = "CUST-SUPPLY"


def restock_cost(item, quantity, unit_price, express=False):
    """Estimate the tax-inclusive cost to restock an item from the supplier."""
    order = Order(RESTOCK_SUPPLIER, item, quantity, unit_price, express)
    return price_order(order, apply_tax=True)


def clearance_price(item, quantity, unit_price):
    """Estimate a no-tax clearance price for overstocked items."""
    order = Order(RESTOCK_SUPPLIER, item, quantity, unit_price, express=False)
    return price_order(order, apply_tax=False)


def restock(item, quantity):
    if item not in STOCK:
        STOCK[item] = 0
    STOCK[item] += quantity


def stock_level(item):
    return STOCK.get(item, 0)


def is_low_stock(item):
    return stock_level(item) < LOW_STOCK_THRESHOLD
