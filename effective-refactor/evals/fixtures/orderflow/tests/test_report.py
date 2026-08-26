import unittest

from orderflow import notify
from orderflow.core import Order
from orderflow.report import daily_total, grand_summary, order_lines, tax_rate_display


class TestReport(unittest.TestCase):
    def setUp(self):
        notify.clear_alerts()
        self.orders = [
            Order("CUST-001", "widget", 2, 10.0),
            Order("CUST-002", "gadget", 1, 5.0),
        ]

    def test_daily_total_sums_all_orders(self):
        total = daily_total(self.orders)
        self.assertGreater(total, 0)
        self.assertEqual(total, round(27.0 + 10.8, 2))

    def test_order_lines_one_per_order(self):
        lines = order_lines(self.orders)
        self.assertEqual(len(lines), 2)
        self.assertIn("CUST-001", lines[0])

    def test_daily_total_empty_list_is_zero(self):
        self.assertEqual(daily_total([]), 0.0)

    def test_tax_rate_display_formats_percent(self):
        self.assertEqual(tax_rate_display(), "8.0%")

    def test_grand_summary_contains_total_and_fires_alert(self):
        summary = grand_summary(self.orders)
        self.assertIn("Daily total", summary)
        self.assertTrue(any("Daily report generated" in e for e in notify.ALERT_LOG))


if __name__ == "__main__":
    unittest.main()
