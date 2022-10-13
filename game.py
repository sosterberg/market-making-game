import random
import threading
from orderbook import OrderBook
import client_communication_tool


class Game:
    def __init__(self, client_communicator):
        self.client_communicator = client_communicator
        self.started = False
        self.clients = set()
        self.client_to_id = {}
        self.client_to_secret = {}
        self.fair_price = None
        self.market_open = False
        self.orderbook = None
        self.orderbook_is_dark = False

    def start(self, clients, duration, orderbook_is_dark):
        if not self.started:
            self.started = True
            self.client_to_secret.clear()

            self.clients = clients
            client_id = 1
            for client in self.clients:
                self.client_to_secret[client] = random.randint(1, 10)
                self.client_to_id[client] = client_id
                client_id += 1
            self.fair_price = sum(self.client_to_secret.values())
            self.market_open = True
            self.orderbook = OrderBook()
            self.orderbook_is_dark = orderbook_is_dark

            self.schedule_game_end(duration)
            return True
        return False

    def stop(self):
        if self.started:
            self.started = False
            return True
        return False

    def is_started(self):
        return self.started

    def handle_message(self, client, message):
        if client not in self.clients:
            return [(client, "You are not part of a started game. Wait until one starts.")]
        else:
            if not self.started:
                return None
            elif self.make_order(client, message):
                messages = []
                for client in self.clients:
                    orderbook_status = self.orderbook.orders(is_dark=self.orderbook_is_dark) + self.orderbook.status(client)
                    messages.append((client, orderbook_status))
                return messages
            return [(client, "You are part of the game, congratz")]

    def end_game(self):
        self.started = False
        self.client_communicator.add_persistent_information(self.clients, self.orderbook.result(self.fair_price, self.client_to_id))
        self.client_communicator.send_to_clients(self.clients, "Game is over!")

    def schedule_game_end(self, duration):
        threading.Timer(duration, self.end_game).start()

    def make_order(self, client, message):
        if message[0] not in ['b', 's'] or not message[1:].isnumeric():
            return False

        price = int(message[1:])

        if message[0] == 'b':
            if client not in self.orderbook.client2bid:
                order_id = self.orderbook.add_order(client, True, 1, price)
                self.orderbook.client2bid[client] = order_id
            else:
                order_id = self.orderbook.client2bid[client]
                self.orderbook.update_order(client, order_id, 1, price)

        elif message[0] == 's':
            if client not in self.orderbook.client2ask:
                order_id = self.orderbook.add_order(client, False, 1, price)
                self.orderbook.client2ask[client] = order_id
            else:
                order_id = self.orderbook.client2ask[client]
                self.orderbook.update_order(client, order_id, 1, price)

        return True
