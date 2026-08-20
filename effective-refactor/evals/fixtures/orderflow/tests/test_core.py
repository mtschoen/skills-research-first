import unittest

from orderflow.core import Order, batch_proc, price_order


class TestProc(unittest.TestCase):
    def test_no_tax_standard_shipping(self):
        order = Order("CUST-001", "widget", 2, 10.0)
        # subtotal 20, below discount threshold, +5 shipping, no tax
        self.assertEqual(price_order(order, apply_tax=False), 25.0)

    def test_with_tax(self):
        order = Order("CUST-001", "widget", 2, 10.0)
        # (20 + 5) * 1.08
        self.assertEqual(price_order(order, apply_tax=True), 27.0)

    def test_express_shipping_multiplier(self):
        order = Order("CUST-001", "widget", 2, 10.0, express=True)
        # (20 + 5*2.5) = 32.5, no tax
        self.assertEqual(price_order(order, apply_tax=False), 32.5)

    def test_discount_applied_at_threshold(self):
        order = Order("CUST-001", "widget", 10, 20.0)
        # subtotal 200 >= 100 -> discount 10% -> 180, + shipping 5 = 185
        self.assertEqual(price_order(order, apply_tax=False), 185.0)

    def test_no_discount_below_threshold(self):
        order = Order("CUST-001", "widget", 5, 10.0)
        # subtotal 50, below threshold, + shipping 5 = 55
        self.assertEqual(price_order(order, apply_tax=False), 55.0)

    def test_batch_proc_preserves_order(self):
        orders = [
            Order("CUST-001", "widget", 1, 10.0),
            Order("CUST-002", "gadget", 2, 5.0),
        ]
        results = batch_proc(orders, apply_tax=False)
        self.assertEqual(
            results,
            [
                price_order(orders[0], apply_tax=False),
                price_order(orders[1], apply_tax=False),
            ],
        )


if __name__ == "__main__":
    unittest.main()
