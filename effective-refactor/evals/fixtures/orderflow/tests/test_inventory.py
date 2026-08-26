import unittest

from orderflow import inventory


class TestInventory(unittest.TestCase):
    def setUp(self):
        self._stock_snapshot = dict(inventory.STOCK)

    def tearDown(self):
        inventory.STOCK.clear()
        inventory.STOCK.update(self._stock_snapshot)

    def test_restock_cost_includes_tax(self):
        cost = inventory.restock_cost("widget", 2, 10.0)
        self.assertEqual(cost, 27.0)

    def test_clearance_price_excludes_tax(self):
        price = inventory.clearance_price("widget", 2, 10.0)
        self.assertEqual(price, 25.0)

    def test_restock_increases_stock(self):
        before = inventory.STOCK["gadget"]
        inventory.restock("gadget", 10)
        self.assertEqual(inventory.STOCK["gadget"], before + 10)

    def test_restock_creates_new_item(self):
        inventory.restock("thingamajig", 5)
        self.assertEqual(inventory.STOCK["thingamajig"], 5)

    def test_is_low_stock_true_below_threshold(self):
        inventory.STOCK["gizmo"] = 2
        self.assertTrue(inventory.is_low_stock("gizmo"))

    def test_is_low_stock_false_above_threshold(self):
        inventory.STOCK["gizmo"] = 50
        self.assertFalse(inventory.is_low_stock("gizmo"))


if __name__ == "__main__":
    unittest.main()
