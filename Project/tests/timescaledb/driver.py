import psycopg
from io import StringIO
from base_driver import BaseDriver

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.user = kwargs.get("user", "postgres")
        self.password = kwargs.get("password", "")
        self.database = kwargs.get("database", "postgres")
        self.conn = None
        self.cur = None

    def connect(self):
        conninfo = f"host={self.host} port={self.port} dbname={self.database} user={self.user}"
        if self.password:
            conninfo += f" password={self.password}"
        
        self.conn = psycopg.connect(conninfo)
        self.cur = self.conn.cursor()

    def prepare_schema(self):
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                GpsTime TIMESTAMPTZ NOT NULL,
                VehicleID TEXT,
                Longitude DOUBLE PRECISION,
                Latitude DOUBLE PRECISION,
                SpeedGps DOUBLE PRECISION,
                SpeedTach DOUBLE PRECISION,
                SpeedCan DOUBLE PRECISION,
                TachoGps DOUBLE PRECISION,
                TachoTach DOUBLE PRECISION,
                ModeDrive INT,
                SpreadingMode INT,
                Plow INT,
                Gram INT,
                WidthLeft DOUBLE PRECISION,
                WidthRight DOUBLE PRECISION,
                SumSalt DOUBLE PRECISION,
                SumInert DOUBLE PRECISION,
                SumBrine DOUBLE PRECISION,
                Cuts1 INT,
                Cuts2 INT,
                Cuts3 INT,
                CentralBroom INT,
                LeftBroom INT,
                RightBroom INT,
                Turbine INT,
                RunningShaft INT,
                LeftFlushing INT,
                RightFlushing INT,
                CentralFlushing INT,
                Misting INT,
                Pump INT,
                LightOn INT,
                ModeArrow INT,
                AkuVoltage DOUBLE PRECISION,
                RampUp INT,
                Crash INT,
                TempAir DOUBLE PRECISION,
                TempRoad DOUBLE PRECISION,
                Revs DOUBLE PRECISION,
                RevsExtension INT,
                Fuel DOUBLE PRECISION,
                LevelPHM DOUBLE PRECISION,
                PowerVoltage DOUBLE PRECISION,
                Lighthouse INT,
                orig_id BIGINT,
                orig_time TEXT,
                orig_topic TEXT,
                CreatedTime TEXT,
                GsmSignal INT,
                SatelliteCount INT,
                LicensePlate TEXT,
                VehicleType INT,
                Company TEXT,
                Technology INT,
                Ignition INT
            )
        """)
        
        self.cur.execute(f"""
            SELECT create_hypertable('{self.table}', 'GpsTime', if_not_exists => TRUE)
        """)
        
        self.cur.execute(f"TRUNCATE TABLE {self.table}")
        self.conn.commit()

    def insert_batch(self, batch):
            cols = [
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
            
            buf = StringIO()
            for r in batch:
                row = []
                for c in cols:
                    val = r[c]
                    if c == "GpsTime":
                        row.append(val.strftime("%Y-%m-%d %H:%M:%S.%f"))
                    else:
                        row.append(str(val))
                buf.write(",".join(row) + "\n")
            
            buf.seek(0)
            col_str = ",".join(cols)
            
            try:
                with self.cur.copy(f"COPY {self.table} ({col_str}) FROM STDIN WITH (FORMAT csv)") as copy:
                    copy.write(buf.read())
                self.conn.commit()
                return len(batch)
            except Exception as e:
                self.conn.rollback()
                raise

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()