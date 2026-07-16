from datetime import timezone
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError
from base_driver import BaseDriver

class Driver(BaseDriver):
    def __init__(self, host, port, table, **kwargs):
        super().__init__(host, port, table, **kwargs)
        self.database = kwargs.get("database", "test")
        self.user = kwargs.get("user", "")
        self.password = kwargs.get("password", "")
        self.client = None
        self.coll = None

    def connect(self):
        if self.user and self.password:
            uri = f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/"
        else:
            uri = f"mongodb://{self.host}:{self.port}/"
        
        self.client = MongoClient(uri, maxPoolSize=10)
        self.db = self.client[self.database]
        self.coll = self.db[self.table]

    def prepare_schema(self):
        self.coll.drop()
        
        try:
            self.db.create_collection(
                self.table,
                timeseries={
                    "timeField": "GpsTime",
                    "metaField": "VehicleID",
                    "granularity": "seconds"
                }
            )
            
        # Index for query performance
        self.coll.create_index([("GpsTime", ASCENDING), ("VehicleID", ASCENDING)])

    def insert_batch(self, batch):
        # Convert datetime to timezone-aware UTC for MongoDB
        for r in batch:
            ts = r["GpsTime"]
            if ts.tzinfo is None:
                r["GpsTime"] = ts.replace(tzinfo=timezone.utc)
            else:
                r["GpsTime"] = ts.astimezone(timezone.utc)
        
        try:
            result = self.coll.insert_many(batch, ordered=False)
            return len(result.inserted_ids)
        except BulkWriteError as bwe:
            write_errors = bwe.details.get("writeErrors", [])
            inserted = bwe.details.get("nInserted", 0)
            if inserted > 0:
                return inserted
            raise

    def close(self):
        if self.client:
            self.client.close()