import socket
import argparse
import _thread
import logging
import random
import re
import orderbook as ob
import time
import sys


LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-server.log"
CONSOLE_FORMATTER_PATTERN = "%(message)s'"
HOST = "127.0.0.1"
PORT = 1234
DURATION_SECONDS = 60
QUOTE_PATTERN = re.compile("([0-9]*)\@([0-9]*)\|([0-9]*)\@([0-9]*)")
MARKET_CLOSED_MSG = "Sorry, the market has closed\n"
HELP_MSG = """
--- MARKET MAKING GAME ---
Every participant gets a secret number between 1 and 10 (inclusive).
The goal is to trade the security *sum of the secrets*.

To quote, use the following format <bid volume>@<bid price>|<ask price>@<ask volume>, e.g. 10@20|30@40 would quote
10 units at 20 bid and 40 units at 30 offered.

Shortcuts
help: See this message again. 
status: Get the current status of your account
up/down/in/out: shift all your orders up, down, in our out

Good luck!

"""

connection2secret = {}
connection2id = {}
connection2bid = {}
connection2ask = {}
orderbook = ob.OrderBook()
market_closed = False


def setup_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(CONSOLE_FORMATTER_PATTERN)
    console.setFormatter(formatter)
    LOG.addHandler(console)


def handle_quote(connection, bid_volume, bid, ask, ask_volume):
    if bid:
        if connection not in connection2bid:
            order_id = orderbook.add_order(connection, True, bid_volume, bid)
            connection2bid[connection] = order_id
        else:
            order_id = connection2bid[connection]
            orderbook.update_order(connection, order_id, bid_volume, bid)

    if ask:
        if connection not in connection2ask:
            order_id = orderbook.add_order(connection, False, ask_volume, ask)
            connection2ask[connection] = order_id
        else:
            order_id = connection2ask[connection]
            orderbook.update_order(connection, order_id, ask_volume, ask)


def parse_quote(quote):
    quotes = quote.split(",")
    bid_volume = 1
    ask_volume = 1
    bid = None
    ask = None
    for q in quotes:
        side_and_price = q.split("@")
        if len(side_and_price) == 2:
            side, price = side_and_price
            if side.strip().lower() in ["b", "buy"] and price.strip().isnumeric():
                bid = int(price)
            elif side.strip().lower() in ["s", "sell"] and price.strip().isnumeric():
                ask = int(price)
        else:
            LOG.error("Invalid quote: expected <b(uy)/s(ell)>@<price>, e.g. b@12, sell@14")
            return None

    return bid_volume, bid, ask, ask_volume


def handle_status_request(message):
    return message.lower() in ["status", "s"]


def handle_help_request(message):
    return message.lower() in ["help", "h"]


def handle_off_request(message):
    return message.lower() in ["off"]


def handle_instruction(connection, message):
    m = message.lower()
    if m not in ["up", "u", "down", "d", "out", "o", "in", "i"]:
        return False

    bid_order_id = connection2bid.get(connection)
    ask_order_id = connection2ask.get(connection)
    bid_order = ob.Order.id2order.get(bid_order_id)
    ask_order = ob.Order.id2order.get(ask_order_id)

    if bid_order is not None:
        if m in ["up", "u", "in", "i"]:
            price = min(bid_order.price + 1, ask_order.price - 1) if ask_order else bid_order.price + 1
            orderbook.update_order(connection, order_id=bid_order_id, price=price)
        if m in ["down", "d", "out", "o"]:
            orderbook.update_order(connection, order_id=bid_order_id, price=bid_order.price - 1)
    if ask_order_id is not None:
        ask_order = ob.Order.id2order[ask_order_id]
        if m in ["up", "u", "out", "o"]:
            orderbook.update_order(connection, order_id=ask_order_id, price=ask_order.price + 1)
        if m in ["down", "d", "in", "i"]:
            price = max(ask_order.price - 1, bid_order.price + 1) if bid_order else ask_order.price - 1
            orderbook.update_order(connection, order_id=ask_order_id, price=price)
    return True


def client_handler(connection):
    secret = random.randint(1, 10)
    connection.sendall(str.encode("You are now connected to the replay server, your secret is {0} ".format(secret)))
    connection2secret[connection] = secret
    connection2id[connection] = len(connection2id) + 1
    while True:
        data = connection.recv(2048)
        message = data.decode("utf-8")
        if market_closed:
            true_price = sum(connection2secret.values())
            reply = MARKET_CLOSED_MSG + get_result()
        elif handle_status_request(message):
            reply = str(orderbook) + orderbook.status(connection)
        elif handle_help_request(message):
            reply = HELP_MSG
        elif handle_off_request(message):
            if connection in connection2bid:
                orderbook.cancel_order(connection, connection2bid[connection])
            if connection in connection2ask:
                orderbook.cancel_order(connection, connection2ask[connection])
            reply = str(orderbook) + orderbook.status(connection)
        elif handle_instruction(connection, message):
            reply = str(orderbook) + orderbook.status(connection)
        else:
            quote = parse_quote(message)
            if quote:
                bid_volume, bid, ask, ask_volume = quote
                handle_quote(connection, bid_volume, bid, ask, ask_volume)
                reply = str(orderbook) + orderbook.status(connection)
            else:
                reply = "Faulty quote"
        connection.sendall(str.encode(reply))


def accept_connections(server_socket):
    client, address = server_socket.accept()
    _thread.start_new_thread(client_handler, (client, ))


def start_server(host, port, duration):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
    except socket.error as e:
        print(str(e))
    server_socket.listen()
    LOG.info("Listening for connections...")

    schedule_game_end(duration)
    while True:
        accept_connections(server_socket)


def get_result():
    # TODO Use id instead of connection in orderbook
    return orderbook.result(sum(connection2secret.values()), connection2id)


def handle_game_end(duration):
    time.sleep(duration)
    global market_closed
    market_closed = True
    LOG.info(get_result())


def schedule_game_end(duration):
    _thread.start_new_thread(handle_game_end, (duration,))


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    parser.add_argument("--duration", help="Duration of the game (in seconds)", type=int, default=DURATION_SECONDS)
    args = parser.parse_args()
    LOG.info(f"Starting Market Maker Game Server on {args.host}:{args.port}, market open for {args.duration} seconds.")
    start_server(args.host, args.port, args.duration)
