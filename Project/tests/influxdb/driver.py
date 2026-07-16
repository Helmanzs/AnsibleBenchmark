import gzip
import requests
from base_driver import BaseDriver
from generate_live_data import format_line_protocol_batch

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.token = kwargs.get("password", "")
        self.database = kwargs.get("database", table)
        self.session = None

    def connect(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "text/plain; charset=utf-8",
        })

    def prepare_schema(self):
        pass 

    def insert_batch(self, batch):
        body = format_line_protocol_batch(batch, self.table)
        compressed = gzip.compress(body.encode())
        
        url = f"http://{self.host}:{self.port}/api/v3/write_lp"
        params = {
            "db": self.database,
            "precision": "auto",
            "no_sync": "true",
            "accept_partial": "false"
        }
        
        resp = self.session.post(url, params=params, data=compressed, headers={"Content-Encoding": "gzip"})
        if not resp.ok:
            raise RuntimeError(f"write_lp failed [{resp.status_code}]: {resp.text[:2000]}")
        return len(batch)

    def close(self):
        self.session.close()