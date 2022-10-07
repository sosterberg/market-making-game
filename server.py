import socket
import argparse
import _thread
import logging
import random
import orderbook as ob
import time
import sys


LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-server.log"
CONSOLE_FORMATTER_PATTERN = "%(message)s"
HOST = "127.0.0.1"
PORT = 1234
DURATION_SECONDS = 60
MARKET_CLOSED_MSG = "Sorry, the market has closed\n\r"
HELP_MSG = """
--- MARKET MAKING GAME ---
Every participant gets a secret number between 1 and 10 (inclusive).
The goal is to trade the security *sum of the secrets*.

To quote, use the following format "b20" to buy at 20, "s10" to sell at 10, "q10/20" to buy at 10 and sell at 20

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
orderbook_is_dark = False
clients = []
game_started = False


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
    quote_valid = False
    for q in quotes:
        q = q.strip()
        if q[0] == 'b' or q[0] == 's':
            price = q[1:]
            if price.strip().isnumeric():
                if q[0] == 'b':
                    bid = int(price)
                    quote_valid = True
                else:
                    ask = int(price)
                    quote_valid = True
        elif q[0] == 'q':
            prices = q[1:].split("/")
            if len(prices) == 2:
                q_bid, q_ask = prices
                if q_bid.strip().isnumeric() and q_ask.strip().isnumeric():
                    bid = int(q_bid)
                    ask = int(q_ask)
                    quote_valid = True

        if not quote_valid:
            LOG.error(f"Client sent invalid quote {quote}")
            return None

    return bid_volume, bid, ask, ask_volume


def is_help_request(message):
    return message.lower() in ["help", "h"]


def is_off_request(message):
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


def send_to_client(client, message):
    info_message = f"You are client {connection2id[client]} and your secret is {connection2secret[client]}\n\r"
    client.sendall(str.encode(info_message + message))


def client_handler(connection):
    global orderbook_is_dark
    global game_started

    while True:
        data = connection.recv(2048)
        message = data.decode("utf-8")

        if not game_started:
            send_to_client(connection, "Game has not started yet")
            continue

        if market_closed:
            reply = MARKET_CLOSED_MSG + orderbook.orders(is_dark=orderbook_is_dark) + orderbook.status(connection) + get_result()
        elif is_help_request(message):
            reply = HELP_MSG.replace("\n", "\n\r")
        elif is_off_request(message):
            if connection in connection2bid:
                orderbook.cancel_order(connection, connection2bid[connection])
            if connection in connection2ask:
                orderbook.cancel_order(connection, connection2ask[connection])
            reply = ""
        elif handle_instruction(connection, message):
            reply = ""
        else:
            quote = parse_quote(message)
            if quote:
                bid_volume, bid, ask, ask_volume = quote
                handle_quote(connection, bid_volume, bid, ask, ask_volume)
                for client in clients:
                    orderbook_status = orderbook.orders(is_dark=orderbook_is_dark) + orderbook.status(client)
                    send_to_client(client, orderbook_status)
                reply = ""
            else:
                reply = "Invalid quote: expected <b(uy)/s(ell)>@<price>, e.g. b@12, sell@14"

        reply = orderbook.orders(is_dark=orderbook_is_dark) + orderbook.status(connection) + reply
        send_to_client(connection, reply)


def accept_connections(server_socket):
    global game_started
    global connection2secret
    global connection2id
    client, address = server_socket.accept()
    if game_started:
        LOG.info("GAME IS STARTED. NOT ACCEPTING CONNECTION")
        send_to_client(client, "REJECT")
        client.close()
        return
    clients.append(client)
    LOG.info(f"Client connected. Number of clients is now {len(clients)}")

    secret = random.randint(1, 10)
    connection2secret[client] = secret
    connection2id[client] = len(connection2id) + 1

    send_to_client(client, f"You are now connected to the replay server, your secret is {secret}. Game will begin shortly")
    _thread.start_new_thread(client_handler, (client,))


def start_server(host, port):
    global game_started
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((host, port))
    except socket.error as e:
        print(str(e))
    server_socket.listen()
    LOG.info("Listening for connections...")

    while not game_started:
        accept_connections(server_socket)


def get_result():
    # TODO Use id instead of connection in orderbook
    return orderbook.result(sum(connection2secret.values()), connection2id)


def handle_game_end(duration):
    time.sleep(duration)
    global market_closed
    market_closed = True
    LOG.info(get_result())
    for client in clients:
        send_to_client(client, orderbook.orders(is_dark=orderbook_is_dark) + orderbook.status(client) + get_result())


def schedule_game_end(duration):
    _thread.start_new_thread(handle_game_end, (duration,))


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    parser.add_argument("--duration", help="Duration of the game (in seconds)", type=int, default=DURATION_SECONDS)
    parser.add_argument("--orderbook-is-dark", help="Hide the orderbook from traders", action="store_true")
    args = parser.parse_args()
    orderbook_is_dark = args.orderbook_is_dark
    print(f"Order book is{' not' if not orderbook_is_dark else ''} dark")
    LOG.info(f"Starting Market Maker Game Server on {args.host}:{args.port}, market open for {args.duration} seconds.")
    LOG.info("Type 'start' to start the game")

    _thread.start_new_thread(start_server, (args.host, args.port))
    while True:
        command = input("")
        if command == "start":
            game_started = True
            LOG.info("Game is now started")
            for receiver in clients:
                send_to_client(receiver, f"The game has begun")
            LOG.info(f"Fair price is {sum(connection2secret.values())}")
            schedule_game_end(args.duration)
