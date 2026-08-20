"""Command-line demo entry point."""

from .core import Order, proc
from .orders import handle_order_input
from .report import grand_summary


def run_demo():
    sample_lines = [
        "CUST-001,widget,3,9.99,no",
        "CUST-002,gadget,1,49.50,yes",
    ]
    for line in sample_lines:
        print(handle_order_input(line))
        print()

    demo_orders = [
        Order("CUST-003", "gizmo", 2, 15.0),
        Order("CUST-004", "widget", 5, 9.99, express=True),
    ]
    print(grand_summary(demo_orders))
    print(f"Single order total: {proc(demo_orders[0], True)}")


if __name__ == "__main__":
    run_demo()
