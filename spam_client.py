import _thread
import socket
import logging
import argparse
import sys
import os
import random
import time

LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-client.log"
HOST = "127.0.0.1"
PORT = 1234
CONSOLE_FORMATTER_PATTERN = "%(message)s'"


def setup_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(CONSOLE_FORMATTER_PATTERN)
    console.setFormatter(formatter)
    LOG.addHandler(console)


def listener_thread(client_socket):
    while True:
        response = client_socket.recv(2048)
        os.system('cls||clear')
        LOG.info(response.decode("utf-8"))
        if response == "ENDGAME":
            quit()


def main(host, port):
    client_socket = socket.socket()
    LOG.info("Waiting for connections")
    try:
        client_socket.connect((host, port))
    except socket.error as e:
        LOG.error(str(e))

    _thread.start_new_thread(listener_thread, (client_socket, ))

    while True:
        bs = ["b", "s"]
        side = random.choice(bs)
        price = random.randint(1, 30)
        # input_string = input("Your quote: ")
        input_string = side + "@" + str(price)
        time.sleep(10)
        if not input_string:
            continue
        client_socket.send(str.encode(input_string))
    client_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    args = parser.parse_args()
    main(args.host, args.port)
