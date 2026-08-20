"""Order intake: parsing raw input lines into orders and receipts."""

from .constants import CUSTOMER_ID_PREFIX
from .core import Order, price_order
from .inventory import STOCK, is_low_stock
from .notify import send_page


def handle_order_input(raw_line):
    """Parse, validate, price, and format a single raw order line.

    Expected format:
        "customer_id,item,quantity,unit_price,express"

    Returns a formatted receipt string. Raises ValueError on malformed
    or invalid input.
    """
    # --- parsing ---
    if not raw_line or not raw_line.strip():
        raise ValueError("empty order line")

    fields = raw_line.strip().split(",")
    if len(fields) != 5:
        raise ValueError(f"expected 5 fields, got {len(fields)}: {raw_line!r}")

    customer_id_raw, item_raw, quantity_raw, unit_price_raw, express_raw = fields

    customer_id = customer_id_raw.strip()
    item = item_raw.strip()

    try:
        quantity = int(quantity_raw.strip())
    except ValueError:
        raise ValueError(f"quantity must be an integer, got {quantity_raw!r}")

    try:
        unit_price = float(unit_price_raw.strip())
    except ValueError:
        raise ValueError(f"unit_price must be a number, got {unit_price_raw!r}")

    express_token = express_raw.strip().lower()
    if express_token in ("1", "true", "yes", "y"):
        express = True
    elif express_token in ("0", "false", "no", "n"):
        express = False
    else:
        raise ValueError(
            f"express must be a boolean-like value, got {express_raw!r}"
        )

    # --- validation ---
    if not customer_id.startswith(CUSTOMER_ID_PREFIX):
        raise ValueError(f"customer_id must start with {CUSTOMER_ID_PREFIX!r}")

    if not item:
        raise ValueError("item name cannot be empty")

    if quantity <= 0:
        raise ValueError("quantity must be positive")

    if unit_price <= 0:
        raise ValueError("unit_price must be positive")

    if item in STOCK and STOCK[item] < quantity:
        raise ValueError(
            f"insufficient stock for {item}: have {STOCK[item]}, need {quantity}"
        )

    # --- processing ---
    order = Order(customer_id, item, quantity, unit_price, express)
    quote_total = price_order(order, apply_tax=False)
    final_total = price_order(order, apply_tax=True)

    if item in STOCK:
        STOCK[item] -= quantity
        if is_low_stock(item):
            send_page(f"Low stock for {item}: {STOCK[item]} remaining")

    # --- formatting ---
    lines = [
        f"Receipt for {customer_id}",
        f"  Item: {item} x{quantity} @ ${unit_price:.2f}",
        f"  Shipping: {'express' if express else 'standard'}",
        f"  Quote (no tax): ${quote_total:.2f}",
        f"  Final total (with tax): ${final_total:.2f}",
    ]
    return "\n".join(lines)
