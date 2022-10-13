import logging
from collections import namedtuple

LOG = logging.getLogger(__name__)

Trade = namedtuple("Trade", "is_buy size price")


def position(trades):
    pos = sum([t.size if t.is_buy else -t.size for t in trades])
    return pos


def realized_pnl(trades):
    buys = sum([t.size for t in trades if t.is_buy])
    sells = sum([t.size for t in trades if not t.is_buy])
    realized = min(buys, sells)

    buy_cash = 0
    buy_size_left = realized
    for t in [t for t in trades if t.is_buy]:
        size = min(buy_size_left, t.size)
        buy_cash += size * t.price
        buy_size_left -= size

    sell_cash = 0
    sell_size_left = realized
    for t in [t for t in trades if not t.is_buy]:
        size = min(sell_size_left, t.size)
        sell_cash += size * t.price
        sell_size_left -= size

    return sell_cash - buy_cash


def account_string(trades):
    s = "--- ACCOUNT ---\n\r"
    s += "pos = {0}\n\rpnl = {1}\n\r".format(position(trades), realized_pnl(trades))
    return s


def trades_string(trades):
    s = "--- TRADES ---\n\r"
    for t in trades:
        s += "{0} {1} @ {2}\n\r".format("Buy" if t.is_buy else "Sell", t.size, t.price)
    return s


class OrderBook:

    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.client2trades = {}
        self.client2bid = {}
        self.client2ask = {}

    def orders(self, client=None, is_dark=True):
        bid_prices = sorted(self.bids.keys(), reverse=True)
        ask_prices = sorted(self.asks.keys())
        max_level = max(len(bid_prices), len(ask_prices))
        s = "--- ORDER BOOK ---\n\r"
        if is_dark and client is None:
            return s
        for level in range(max_level):
            if level < len(bid_prices):
                bid_size = sum([o.size for o in self.bids[bid_prices[level]]])
                s += "{0:5} @ {1:5}".format(bid_size, bid_prices[level])
            else:
                s += "             "
            s += " | "
            if level < len(ask_prices):
                ask_size = sum([o.size for o in self.asks[ask_prices[level]]])
                s += "{0:<5} @ {1:<5}".format(ask_prices[level], ask_size)
            s += "\n\r"
        return s

    def status(self, client):
        trades = self.client2trades.get(client, [])
        return account_string(trades) + trades_string(trades)

    def result(self, true_price, client2id):
        s = "--- RESULT ---\n\r"
        for client, id in client2id.items():
            trades = self.client2trades.get(client, [])
            pos = sum([t.size if t.is_buy else -t.size for t in trades])
            if pos != 0:
                trades.append(Trade(pos < 0, abs(pos), true_price))
            pnl = realized_pnl(trades)
            s += f"P/L for client {client2id[client]}: {pnl}\n\r"
        return s

    def add_order(self, client_id, is_bid, size, price):
        """ Add an order to the order book.

        Returns order_id upon success, otherwise None
        """

        order = Order(client_id, is_bid, size, price)
        self._match(order)
        if order.size == 0:
            return order.id

        if is_bid:
            self.bids.setdefault(price, []).append(order)
            return order.id
        else:
            self.asks.setdefault(price, []).append(order)
            return order.id

    def update_order(self, client_id, order_id, size=None, price=None):
        if order_id in Order.id2order.keys():
            order = Order.id2order[order_id]
            if order.is_bid:
                if order.price in self.bids:
                    if order in self.bids[order.price]:
                        self.bids[order.price].remove(order)
                    if len(self.bids[order.price]) == 0:
                        del self.bids[order.price]
                order.update(size=size, price=price)
                self._match(order)
                if order.size > 0:
                    self.bids.setdefault(order.price, []).append(order)
            else:
                if order.price in self.asks:
                    if order in self.asks[order.price]:
                        self.asks[order.price].remove(order)
                    if len(self.asks[order.price]) == 0:
                        del self.asks[order.price]
                order.update(size=size, price=price)
                self._match(order)
                if order.size > 0:
                    self.asks.setdefault(order.price, []).append(order)

    def cancel_order(self, client_id, order_id):
        if order_id in Order.id2order.keys():
            order = Order.id2order[order_id]
            if order.is_bid:
                if order.price in self.bids:
                    if order in self.bids[order.price]:
                        self.bids[order.price].remove(order)
                    if len(self.bids[order.price]) == 0:
                        del self.bids[order.price]
            else:
                if order.price in self.asks:
                    if order in self.asks[order.price]:
                        self.asks[order.price].remove(order)
                    if len(self.asks[order.price]) == 0:
                        del self.asks[order.price]

    def _match(self, order):
        fills = []
        if order.is_bid:
            while True:
                if len(self.asks) == 0 or order.size == 0:
                    break
                min_ask = min(self.asks.keys())
                if order.price >= min_ask:
                    for opposite_order in self.asks[min_ask]:
                        if order.size >= opposite_order.size:
                            self.asks[min_ask].remove(opposite_order)
                            if len(self.asks[min_ask]) == 0:
                                del self.asks[min_ask]
                            fills.append((order, opposite_order, opposite_order.size, min_ask))
                            order.update(size=order.size - opposite_order.size)
                        else:
                            fills.append((order, opposite_order, order.size, min_ask))
                            opposite_order.update(size=opposite_order.size - order.size)
                            order.update(size=0)
                            break
                else:
                    break
        else:
            while True:
                if len(self.bids) == 0 or order.size == 0:
                    break
                max_bid = max(self.bids.keys())
                if order.price <= max_bid:
                    for opposite_order in self.bids[max_bid]:
                        if order.size >= opposite_order.size:
                            self.bids[max_bid].remove(opposite_order)  #  TODO: Remove order from Order.id2order
                            if len(self.bids[max_bid]) == 0:
                                del self.bids[max_bid]
                            fills.append((opposite_order, order, opposite_order.size, max_bid))
                            order.update(size=order.size - opposite_order.size)
                        else:
                            fills.append((opposite_order, order, order.size, max_bid))
                            opposite_order.update(size=opposite_order.size - order.size)
                            order.update(size=0)
                            break
                else:
                    break
        self.handle_fills(fills)

    def handle_fills(self, fills):
        for buy_order, sell_order, size, price in fills:
            self.client2trades.setdefault(buy_order.client_id, []).append(Trade(True, size, price))
            self.client2trades.setdefault(sell_order.client_id, []).append(Trade(False, size, price))


class Order:
    next_valid_id = 1
    id2order = {}

    def __init__(self, client_id, is_bid, size, price):
        self.client_id = client_id
        self.is_bid = is_bid
        self.size = size
        self.price = price
        Order.next_valid_id += 1
        self.id = Order.next_valid_id
        Order.id2order[self.id] = self

    def update(self, size=None, price=None):
        if size is not None:
            self.size = size
        if price is not None:
            self.price = price