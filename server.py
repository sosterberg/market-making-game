import socket
import argparse
import _thread
import logging
import sys
from client_communication_tool import ClientCommunicator

from game import Game

LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-server.log"
CONSOLE_FORMATTER_PATTERN = "%(message)s"
HOST = "127.0.0.1"
PORT = 1234
DURATION_SECONDS = 10

connected_clients = set()
client_communicator = ClientCommunicator()
game = Game(client_communicator)


def error_log(msg):
    LOG.error(str(msg))


def info_log(msg):
    LOG.info(str(msg))


def is_help_request(message):
    return message.lower() in ["help", "h"]


def client_handler(connection):
    global game

    client_communicator.send_to_clients(connection, f"You are connected to the server. {'Wait for a game to start.' if not game.is_started() else 'There is an ongoing game, you will get to join the next one.'}")

    while True:
        try:
            data = connection.recv(2048)
        except (ConnectionAbortedError, ConnectionResetError):
            error_log(f"Client {connection} lost connection to the server")
            connected_clients.remove(connection)
            return
        message = data.decode("utf-8")

        messages_to_send = game.handle_message(connection, message)
        if messages_to_send is not None:
            for message_to_send in messages_to_send:
                receiver, text = message_to_send
                client_communicator.send_to_clients(receiver, text)


def accept_client(server_socket):
    client, _ = server_socket.accept()

    connected_clients.add(client)

    LOG.info(f"Client connected. Number of clients is now {len(connected_clients)}")
    _thread.start_new_thread(client_handler, (client,))


def accept_connecting_clients(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(("", port))
    except socket.error as e:
        LOG.error(str(e))
    server_socket.listen()
    LOG.info("Listening for connections...")

    while True:
        accept_client(server_socket)


def setup_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(CONSOLE_FORMATTER_PATTERN)
    console.setFormatter(formatter)
    LOG.addHandler(console)


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    parser.add_argument("--duration", help="Duration of the game (in seconds)", type=int, default=DURATION_SECONDS)
    parser.add_argument("--orderbook-is-dark", help="Hide the orderbook from traders", action="store_true")
    args = parser.parse_args()

    info_log("Type 'start' to start a new game when all clients have connected")

    _thread.start_new_thread(accept_connecting_clients, (args.host, args.port))
    while True:
        command = input("")
        if command == "start":
            info_log(f"Starting game with {len(connected_clients)} clients")
            game.start(connected_clients, args.duration, args.orderbook_is_dark)
            client_communicator.send_to_clients(connected_clients, "A new game has started")
        elif command == "stop":
            game.stop()
