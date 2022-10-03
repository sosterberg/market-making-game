import unittest
import orderbook
from orderbook import Trade


class MyTestCase(unittest.TestCase):

    def test_empty_orderbook(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        print(ob)

    def test_one_level_orderbook(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        ob.add_order(12, True, 10, 100)
        print(ob)


    def test_two_level_orderbook(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        ob.add_order(12, True, 10, 100)
        ob.add_order(12, True, 11, 102)
        ob.add_order(12, False, 12, 102)
        print(ob)

    def test_two_order_on_same_level_orderbook(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        ob.add_order(12, True, 10, 100)
        ob.add_order(12, True, 20, 100)
        ob.add_order(12, False, 12, 102)
        print(ob)

    def test_updating_order(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        order_id = ob.add_order(12, True, 10, 100)
        print(ob)
        ob.update_order(12, order_id, size=15)
        print(ob)
        ob.update_order(12, order_id, price=150)
        print(ob)

    def test_cancelling_Order(self):
        """Test if we can instantiate an empty orderbook and print it without errors."""
        ob = orderbook.OrderBook()
        order_id1 = ob.add_order(12, True, 10, 100)
        order_id2 = ob.add_order(12, False, 12, 102)
        print(ob)
        ob.cancel_order(12, order_id1)
        print(ob)
        ob.cancel_order(12, order_id2)
        print(ob)

    def test_matching_marketable_buy_order(self):
        ob = orderbook.OrderBook()
        order_id1 = ob.add_order(12, False, 10, 100)
        order_id2 = ob.add_order(12, False, 5, 101)
        print(ob)
        order_id3 = ob.add_order(14, True, 17, 102)
        print(ob)

    def test_matching_marketable_sell_order(self):
        ob = orderbook.OrderBook()
        order_id1 = ob.add_order(12, True, 5, 98)
        order_id2 = ob.add_order(12, True, 15, 97)
        print(ob)
        order_id3 = ob.add_order(14, False, 17, 97)
        print(ob)


    def test_matching_update_order_to_marketable(self):
        ob = orderbook.OrderBook()
        order_id1 = ob.add_order(12, True, 5, 98)
        order_id2 = ob.add_order(12, True, 15, 97)
        print(ob)
        order_id3 = ob.add_order(14, False, 17, 100)
        print(ob)
        ob.update_order(14, order_id3, price=97)
        print(ob)

    def test_position(self):
        trades = [Trade(True, 10, 100), Trade(False, 5, 110)]
        pos = orderbook.position(trades)
        self.assertEqual(pos, 5)
        self.assertEqual(orderbook.position([]), 0)

    def test_realized_pnl(self):
        trades = [Trade(True, 10, 100), Trade(False, 5, 110)]
        rpl = orderbook.realized_pnl(trades)
        self.assertEqual(rpl, 50)

    def test_realized_pnl_causality(self):
        trades = [Trade(True, 5, 100), Trade(True, 5, 110), Trade(False, 5, 110)]
        rpl = orderbook.realized_pnl(trades)
        self.assertEqual(rpl, 50)

    def test_realized_pnl_negative(self):
        trades = [Trade(True, 5, 110), Trade(False, 4, 90)]
        rpl = orderbook.realized_pnl(trades)
        self.assertEqual(rpl, -80)


if __name__ == '__main__':
    unittest.main()
