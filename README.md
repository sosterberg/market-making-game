# Market Making Game


## Purpose

A simple terminal game to simulate a trading environment.

Each participant gets a secret number between 1 and 10 (inclusive). The object of the game is to trade "the sum of all secrets" by placing buy and sell orders in an global limit order book. After the specified duration the market closes an any open position is closed out at the true sum of all secrets.

The object of the game is to use the private information (your secret) to get the highest P/L - good luck!


## Installation

Not much to consider really (,i told you it was simple..). Running the server would probably need a Python version >=3.6 (some f-strings are used).


## Running

To run the *client* i.e. **trader** against a server with IP and PORT: `python client.py --host IP --port PORT`.

For further details and default values: `python client.py --help`

---


To run the *server* i.e. **market** with IP and PORT, open for a DURATION: `python server.py --host IP --port PORT --duration DURATION`.

If the orderbook should be dark i.e. the orders are not visible to traders, specify flag `--orderbook-is-dark`  

Type "start" in the server to start a new game.

For further details and default values: `python server.py --help`


## Instructions

Press the 'help' button in the client to get help.

