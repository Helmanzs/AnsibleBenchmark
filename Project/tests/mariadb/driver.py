import datetime
import mariadb
from base_driver import BaseDriver

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.user = kwargs.get("user", "root")
        self.password = kwargs.get("password", "")
        self.database = kwargs.get("database", "test")

    def connect(self):
        self.conn = mariadb.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=False
        )
        self.cur = self.conn.cursor()

    def prepare_schema(self):
        self.cur.execute(f"TRUNCATE TABLE {self.table}")
        self.conn.commit()

    def insert_batch(self, batch):
        cols = [
            "orig_id","orig_time","orig_topic","CreatedTime","GpsTime",
            "GsmSignal","SatelliteCount","LicensePlate","VehicleType","Company",
            "VehicleID","Technology","Ignition","Longitude","Latitude",
            "SpeedGps","SpeedTach","SpeedCan","TachoGps","TachoTach",
            "ModeDrive","SpreadingMode","Plow","Gram","WidthLeft","WidthRight",
            "SumSalt","SumInert","SumBrine","Cuts1","Cuts2","Cuts3",
            "CentralBroom","LeftBroom","RightBroom","Turbine","RunningShaft",
            "LeftFlushing","RightFlushing","CentralFlushing","Misting","Pump",
            "LightOn","ModeArrow","AkuVoltage","RampUp","Crash",
            "TempAir","TempRoad","Revs","RevsExtension","Fuel","LevelPHM",
            "PowerVoltage","Lighthouse"
        ]
        placeholders = ",".join(["?"] * len(cols))
        sql = f"INSERT INTO {self.table} ({','.join(cols)}) VALUES ({placeholders})"
        
        rows = []
        for r in batch:
            row = []
            for c in cols:
                val = r[c]
                if isinstance(val, (datetime.datetime, datetime.date)):
                    row.append(val)
                else:
                    row.append(val)
            rows.append(tuple(row))
        
        self.cur.executemany(sql, rows)
        self.conn.commit()
        return len(batch)

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()