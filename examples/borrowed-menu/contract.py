"""One behavior contract, unchanged between snapshots."""
import unittest

from cafe import MenuService, receipt


class MenuContract(unittest.TestCase):
    def test_default_menu(self):
        self.assertEqual(receipt(MenuService().menu_for()), "soup, bread")

    def test_special_is_added(self):
        self.assertEqual(receipt(MenuService().menu_for("cake")), "soup, bread, cake")

    def test_next_customer_gets_default_menu(self):
        service = MenuService()
        first = service.menu_for("cake")
        second = service.menu_for()
        print("First customer:", receipt(first))
        print("Second customer:", receipt(second))
        self.assertEqual(receipt(second), "soup, bread")

    def test_customer_menus_are_independent(self):
        service = MenuService()
        first = service.menu_for()
        second = service.menu_for("cake")
        self.assertEqual(receipt(first), "soup, bread")
        self.assertEqual(receipt(second), "soup, bread, cake")
