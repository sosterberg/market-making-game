import _thread
import socket
import logging
import argparse
import sys
import os
import curses


LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-client.log"
HOST = "127.0.0.1"
PORT = 1234
CONSOLE_FORMATTER_PATTERN = "%(message)s"
user_input = ""
latest_output = ""

win = curses.initscr()
win.nodelay(False)
curses.cbreak()


def error_log(msg):
    global latest_output
    global user_input
    latest_output = msg

    msg = msg + '\n\r\n\r\n\r' + user_input

    os.system('clear -x')
    LOG.error(msg)


def info_log(msg):
    global latest_output
    global user_input
    latest_output = msg

    msg = msg + '\n\r\n\r\n\r' + user_input

    os.system('clear -x')
    LOG.info(msg)


def show_user_input():
    global latest_output
    global user_input

    text = latest_output + '\n\r\n\r\n\r' + user_input
    os.system('clear -x')
    LOG.info(text)


def setup_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(CONSOLE_FORMATTER_PATTERN)
    console.setFormatter(formatter)
    LOG.addHandler(console)


def listener_thread(client_socket):
    while True:
        response = client_socket.recv(2048)
        message = response.decode("utf-8")

        if message == "REJECT":
            error_log("Server rejected connection")
            os._exit(1)

        if not message == "":
            info_log(message)


def main(host, port):
    global user_input
    global win
    client_socket = socket.socket()
    info_log("Connecting to server")
    try:
        client_socket.connect((host, port))
    except socket.error as e:
        error_log(str(e))
        return

    _thread.start_new_thread(listener_thread, (client_socket, ))

    user_input = ""
    while True:
        input_char = win.getch()
        if input_char == curses.KEY_ENTER or input_char == 10:
            if not user_input:
                continue
            client_socket.send(str.encode(user_input))
            user_input = ""
        else:
            try:
                decoded_char = chr(input_char)
                if decoded_char.isalnum() or decoded_char in ['@', '/']:
                    user_input = user_input + decoded_char
                elif input_char == 127:
                    user_input = user_input[:-1]
                show_user_input()
            except UnicodeDecodeError as e:
                pass

    client_socket.close()


if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    args = parser.parse_args()
    main(args.host, args.port)
