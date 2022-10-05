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


To run the *server* i.e. **market** with IP and PORT, open for a DURATION: `python client.py --host IP --port PORT --duration DURATION`.

For further details and default values: `python server.py --help`


## Instructions

### Placing orders
Placing an order is done by specifying *\<b(uy)/s(ell)\>@<price>. A buy and a sell order can be simulataneously placed by separating the instruction with a comma. Whitepaces are trimmed.

---

Examples:

*buy @ 12* (equiv. to *b @ 12* and *b@12*)
*sell @ 14* (equiv. to *s @ 14* and *s@14*)
*buy @ 12, sell @ 14* (equiv. to b@12,s@14)


### Updating orders
Orders can be updated by the following commands:
* up/u: move bid and ask price up
* down/d: move bid and ask price down
* in/i: move bid up and ask down
* out/o: move bid down and ask up.
* off: remove orders.

---

Examples, assuming we have orders b@12,s@15 in the market:

* up -> b@13,s@16
* down -> b@11,s@14
* in -> b@13,s@14
* out -> b@11,s@16

### Other useful commands

The orderbook does not update in realtime; to get a snapshot of the current state of the roderbook, the P/L, the current position and the historical trades, type `status`

