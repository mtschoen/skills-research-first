import unittest

from orderflow.core import Order
from orderflow.utils import discount_preview, format_currency, rounded_total


class TestUtils(unittest.TestCase):
    def test_format_currency(self):
        self.assertEqual(format_currency(9.5), "$9.50")

    def test_rounded_total_matches_proc(self):
        order = Order("CUST-001", "widget", 2, 10.0)
        self.assertEqual(rounded_total(order, True), "$27.00")

    def test_discount_preview_below_threshold(self):
        self.assertEqual(discount_preview(50.0), 0.0)

    def test_discount_preview_at_threshold(self):
        self.assertEqual(discount_preview(200.0), 20.0)


if __name__ == "__main__":
    unittest.main()
