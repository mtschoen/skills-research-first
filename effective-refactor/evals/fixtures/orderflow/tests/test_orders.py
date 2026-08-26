import unittest

from orderflow import inventory, notify
from orderflow.orders import handle_order_input


class TestHandleOrderInput(unittest.TestCase):
    def setUp(self):
        self._stock_snapshot = dict(inventory.STOCK)
        notify.clear_alerts()

    def tearDown(self):
        inventory.STOCK.clear()
        inventory.STOCK.update(self._stock_snapshot)

    def test_valid_order_produces_receipt(self):
        receipt = handle_order_input("CUST-001,widget,3,9.99,no")
        self.assertIn("Receipt for CUST-001", receipt)
        self.assertIn("widget x3", receipt)

    def test_valid_order_decrements_stock(self):
        before = inventory.STOCK["widget"]
        handle_order_input("CUST-001,widget,3,9.99,no")
        self.assertEqual(inventory.STOCK["widget"], before - 3)

    def test_bad_customer_prefix_rejected(self):
        with self.assertRaises(ValueError):
            handle_order_input("NOPE-001,widget,1,9.99,no")

    def test_wrong_field_count_rejected(self):
        with self.assertRaises(ValueError):
            handle_order_input("CUST-001,widget,1,9.99")

    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValueError):
            handle_order_input("CUST-001,widget,-1,9.99,no")

    def test_insufficient_stock_rejected(self):
        with self.assertRaises(ValueError):
            handle_order_input("CUST-001,doohickey,50,9.99,no")

    def test_low_stock_triggers_alert(self):
        # doohickey starts at 3, threshold is 5; any purchase drops it below
        # the threshold and should fire an urgent alert.
        handle_order_input("CUST-001,doohickey,1,9.99,no")
        self.assertTrue(any("Low stock" in entry for entry in notify.ALERT_LOG))


if __name__ == "__main__":
    unittest.main()
