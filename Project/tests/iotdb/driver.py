import base64
import requests
from base_driver import BaseDriver
from generate_live_data import format_iotdb_batch

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.user = kwargs.get("user", "root")
        self.password = kwargs.get("password", "root")
        self.session = None

    def connect(self):
        self.session = requests.Session()
        auth_str = f"{self.user}:{self.password}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}",
        })

    def prepare_schema(self):
        # IoTDB creates paths on first insert, no explicit schema needed
        try:
            self.session.post(
                f"http://{self.host}:{self.port}/rest/v1/deleteTimeseries",
                json={"paths": [f"{self.table}.**"]}
            )
        except Exception:
            pass

    def insert_batch(self, batch):
        body = format_iotdb_batch(batch, self.table)
        total_sent = 0
        
        for line in body.splitlines():
            if not line:
                continue
            resp = self.session.post(
                f"http://{self.host}:{self.port}/rest/v1/insertTablet",
                data=line
            )
            resp.raise_for_status()
            total_sent += 1
            
        return len(batch)

    def close(self):
        self.session.close()