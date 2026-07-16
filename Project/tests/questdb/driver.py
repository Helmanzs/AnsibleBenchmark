import socket
from base_driver import BaseDriver
from generate_live_data import format_questdb_batch

class Driver(BaseDriver):
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def prepare_schema(self):
        pass  # auto-created on first ILP insert

    def insert_batch(self, batch):
        payload = format_questdb_batch(batch, self.table) + "\n"
        self.sock.sendall(payload.encode())
        return len(batch)

    def close(self):
        self.sock.close()