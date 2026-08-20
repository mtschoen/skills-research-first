"""Core order model and total computation."""

from .constants import PRICING


class Order:
    """A single line-item order."""

    def __init__(self, customer_id, item, quantity, unit_price, express=False):
        self.customer_id = customer_id
        self.item = item
        self.quantity = quantity
        self.unit_price = unit_price
        self.express = express

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __repr__(self):
        return (
            f"Order({self.customer_id!r}, {self.item!r}, {self.quantity}, "
            f"{self.unit_price}, express={self.express})"
        )


def proc(order, flag):
    """Compute the final total for an order.

    ``flag`` controls whether tax is applied: when True, tax is added on
    top of the discounted subtotal plus shipping. When False, the total
    is computed without tax (used for quick quotes).
    """
    subtotal = order.subtotal

    if subtotal >= PRICING["discount_threshold"]:
        subtotal -= subtotal * PRICING["discount_rate"]

    shipping = PRICING["shipping_flat"]
    if order.express:
        shipping *= PRICING["express_multiplier"]

    total = subtotal + shipping

    if flag:
        total += total * PRICING["tax_rate"]

    return round(total, 2)


def batch_proc(orders, flag):
    """Compute totals for a batch of orders, preserving order."""
    return [proc(order, flag) for order in orders]
