from base_driver import BaseDriver
from clickhouse_driver import Client

class Driver(BaseDriver):
    def connect(self):
        self.client = Client(host=self.host, port=self.port)

    def prepare_schema(self):
        self.client.execute(f"DROP TABLE IF EXISTS {self.table}")
        self.client.execute(f"""
            CREATE TABLE {self.table} (
                GpsTime DateTime64(3),
                VehicleID String,
                Longitude Float64,
                Latitude Float64,
                SpeedGps Float64,
                SpeedTach Float64,
                SpeedCan Float64,
                TachoGps Float64,
                TachoTach Float64,
                ModeDrive Int32,
                SpreadingMode Int32,
                Plow Int8,
                Gram Int32,
                WidthLeft Float64,
                WidthRight Float64,
                SumSalt Float64,
                SumInert Float64,
                SumBrine Float64,
                Cuts1 Int8,
                Cuts2 Int8,
                Cuts3 Int8,
                CentralBroom Int8,
                LeftBroom Int8,
                RightBroom Int8,
                Turbine Int8,
                RunningShaft Int8,
                LeftFlushing Int8,
                RightFlushing Int8,
                CentralFlushing Int8,
                Misting Int8,
                Pump Int8,
                LightOn Int8,
                ModeArrow Int32,
                AkuVoltage Float64,
                RampUp Int8,
                Crash Int8,
                TempAir Float64,
                TempRoad Float64,
                Revs Float64,
                RevsExtension Int8,
                Fuel Float64,
                LevelPHM Float64,
                PowerVoltage Float64,
                Lighthouse Int8,
                orig_id Int64,
                orig_time String,
                orig_topic String,
                CreatedTime String,
                GsmSignal Int32,
                SatelliteCount Int32,
                LicensePlate String,
                VehicleType Int32,
                Company String,
                Technology Int32,
                Ignition Int8
            ) ENGINE = MergeTree()
            ORDER BY (VehicleID, GpsTime)
        """)

    def insert_batch(self, batch):
        columns = [
            "GpsTime","VehicleID","Longitude","Latitude",
            "SpeedGps","SpeedTach","SpeedCan","TachoGps","TachoTach",
            "ModeDrive","SpreadingMode","Plow","Gram","WidthLeft","WidthRight",
            "SumSalt","SumInert","SumBrine","Cuts1","Cuts2","Cuts3",
            "CentralBroom","LeftBroom","RightBroom","Turbine","RunningShaft",
            "LeftFlushing","RightFlushing","CentralFlushing","Misting","Pump",
            "LightOn","ModeArrow","AkuVoltage","RampUp","Crash",
            "TempAir","TempRoad","Revs","RevsExtension","Fuel","LevelPHM",
            "PowerVoltage","Lighthouse","orig_id","orig_time","orig_topic",
            "CreatedTime","GsmSignal","SatelliteCount","LicensePlate",
            "VehicleType","Company","Technology","Ignition"
        ]
        col_str = ",".join(columns)
        rows = [tuple(r[c] for c in columns) for r in batch]
        self.client.execute(f"INSERT INTO {self.table} ({col_str}) VALUES", rows)
        return len(rows)

    def close(self):
        self.client.disconnect()