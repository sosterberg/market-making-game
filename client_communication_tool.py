def to_iterable(clients):
    if not isinstance(clients, list) and not isinstance(clients, set):
        clients = [clients]
    return clients


class ClientCommunicator:
    def __init__(self):
        self.persistent_information = {}

    def add_persistent_information(self, clients, message):
        clients = to_iterable(clients)
        if message:
            for client in clients:
                if client in self.persistent_information:
                    message = f"{self.persistent_information[client]}\n\r{message}"
                self.persistent_information[client] = message

    def send_to_clients(self, clients, message):
        clients = to_iterable(clients)
        if message:
            for client in clients:
                client_message = message
                if client in self.persistent_information:
                    client_message = f"{self.persistent_information[client]}\n\r{message}"
                client.sendall(str.encode(client_message))
