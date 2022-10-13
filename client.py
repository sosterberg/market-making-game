import _thread
import argparse
import logging
import socket
from tkinter import *
from tkinter import ttk
from tkinter import messagebox


HELP_MSG = """
--- MARKET MAKING GAME ---
This is a game where participants trade an instrument.

Each participant will receive a secret number between 1 and 10 (inclusive).

The true value of the instrument is the sum of all the participant secrets.

Trading is done by "market making". I.e. by telling the market (the other participants) what price you are willing to buy/sell the instrument for.

If you want to buy the instrument for the price "20", type "b20" in the command box and press enter.

If you want to sell the instrument for the price "30", type "s30" in the command box and press enter.

Good luck!
"""


def show_help():
    messagebox.showinfo("Help", HELP_MSG)


class Gui:
    def __init__(self):
        self.root = Tk()
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.grid()

        self.connection = None

        self.output_box = Text(self.frm, wrap="none", width=100)
        self.output_box.grid(row=0, columnspan=24)

        self.input_box = Entry(self.frm, width=100)
        self.input_box.grid(row=1, column=0)
        self.input_box.bind("<Return>", self.send_to_server)

        Button(self.frm, command=show_help, text="Help").grid(row=1, column=1)

    def start(self):
        self.root.mainloop()

    def set_output(self, message):
        self.output_box.delete(1.0, "end")
        self.output_box.insert("end", message)

    def set_connection(self, in_connection):
        self.connection = in_connection

    def send_to_server(self, _):
        if self.connection is not None:
            entered_command = self.input_box.get()
            self.connection.send(str.encode(entered_command))
        self.input_box.delete(0, "end")

    def exit(self):
        self.root.destroy()


LOG = logging.getLogger(__name__)
LOG_FILE = "market-making-game-client.log"
CONSOLE_FORMATTER_PATTERN = "%(message)s"
HOST = "127.0.0.1"
PORT = 1234
gui = Gui()


def setup_console_logging():
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(CONSOLE_FORMATTER_PATTERN)
    console.setFormatter(formatter)
    LOG.addHandler(console)


def error_log(msg):
    LOG.error(str(msg))


def info_log(msg):
    LOG.info(str(msg))


def listener_thread(client_socket):
    global gui
    global connection

    connected = True
    while True:
        try:
            response = client_socket.recv(2048)
            connected = True
            message = response.decode("utf-8")

            if message.strip() == "REJECT":
                error_log("Server rejected connection")
                gui.exit()

            if not message == "":
                info_log(message)
                gui.set_output(message)
        except (ConnectionResetError, OSError):
            info_log("Trying to reconnect")
            if connected:
                gui.set_output("Lost connection to server. Trying to reconnect")
            connected = False
            gui.set_connection(None)
            try:
                client_socket.close()
                client_socket = socket.socket()
                client_socket.connect((HOST, PORT))
                gui.set_connection(client_socket)
            except ConnectionRefusedError:
                pass


def connect_to_server(host, port):
    global gui

    client_socket = socket.socket()
    try:
        client_socket.connect((host, port))
        gui.set_connection(client_socket)
        _thread.start_new_thread(listener_thread, (client_socket,))
        return client_socket
    except socket.error as e:
        error_log(e)
        return False


if __name__ == '__main__':
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    setup_console_logging()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="Host name", default=HOST)
    parser.add_argument("--port", help="Port", type=int, default=PORT)
    args = parser.parse_args()

    HOST = args.host
    PORT = args.port

    connect_to_server(args.host, args.port)
    gui.start()
