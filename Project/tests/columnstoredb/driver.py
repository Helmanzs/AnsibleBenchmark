import pymysql
import tempfile
import os
from base_driver import BaseDriver

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.user = kwargs.get("user", "root")
        self.password = kwargs.get("password", "")
        self.database = kwargs.get("database", "test")

    def connect(self):
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            local_infile=True,
            autocommit=True,
        )
        self.cur = self.conn.cursor()

    def prepare_schema(self):
        pass

    def insert_batch(self, batch):
        # Write batch to temp file, then LOAD DATA LOCAL INFILE
        fd, tmp_path = tempfile.mkstemp(suffix='.csv', prefix='bench_')
        try:
            with os.fdopen(fd, 'w') as f:
                for r in batch:
                    vals = [
                        str(r["orig_id"]),
                        r["orig_time"],
                        r["orig_topic"],
                        r["CreatedTime"],
                        r["GpsTime"].strftime("%Y-%m-%d %H:%M:%S.%f"),
                        str(r["GsmSignal"]),
                        str(r["SatelliteCount"]),
                        r["LicensePlate"],
                        str(r["VehicleType"]),
                        r["Company"],
                        r["VehicleID"],
                        str(r["Technology"]),
                        str(r["Ignition"]),
                        str(r["Longitude"]),
                        str(r["Latitude"]),
                        str(r["SpeedGps"]),
                        str(r["SpeedTach"]),
                        str(r["SpeedCan"]),
                        str(r["TachoGps"]),
                        str(r["TachoTach"]),
                        str(r["ModeDrive"]),
                        str(r["SpreadingMode"]),
                        str(r["Plow"]),
                        str(r["Gram"]),
                        str(r["WidthLeft"]),
                        str(r["WidthRight"]),
                        str(r["SumSalt"]),
                        str(r["SumInert"]),
                        str(r["SumBrine"]),
                        str(r["Cuts1"]),
                        str(r["Cuts2"]),
                        str(r["Cuts3"]),
                        str(r["CentralBroom"]),
                        str(r["LeftBroom"]),
                        str(r["RightBroom"]),
                        str(r["Turbine"]),
                        str(r["RunningShaft"]),
                        str(r["LeftFlushing"]),
                        str(r["RightFlushing"]),
                        str(r["CentralFlushing"]),
                        str(r["Misting"]),
                        str(r["Pump"]),
                        str(r["LightOn"]),
                        str(r["ModeArrow"]),
                        str(r["AkuVoltage"]),
                        str(r["RampUp"]),
                        str(r["Crash"]),
                        str(r["TempAir"]),
                        str(r["TempRoad"]),
                        str(r["Revs"]),
                        str(r["RevsExtension"]),
                        str(r["Fuel"]),
                        str(r["LevelPHM"]),
                        str(r["PowerVoltage"]),
                        str(r["Lighthouse"]),
                    ]
                    f.write(",".join(vals) + "\n")

            self.cur.execute(
                f"LOAD DATA LOCAL INFILE '{tmp_path}' INTO TABLE {self.table} "
                "FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n'"
            )
            return len(batch)
        finally:
            os.unlink(tmp_path)

    def close(self):
        self.cur.close()
        self.conn.close()