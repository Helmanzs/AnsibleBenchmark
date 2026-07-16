#!/usr/bin/env python3
import argparse
import csv
import json
import io
import random
import sys
from datetime import datetime, timezone, timedelta
from typing import Iterator, List, Dict, Optional

COMPANIES   = ["sus_uk", "sus_de", "sus_cz", "sus_pl", "sus_at"]
ORIG_TOPICS = ["telemetry/vehicle", "gps/raw", "can/data", "telematics/live"]

IOTDB_MEASUREMENTS = [
    ("orig_id", "INT64"), ("orig_time", "TEXT"), ("orig_topic", "TEXT"),
    ("CreatedTime", "TEXT"), ("GpsTime", "TEXT"), ("GsmSignal", "INT32"),
    ("SatelliteCount", "INT32"), ("LicensePlate", "TEXT"), ("VehicleType", "INT32"),
    ("Company", "TEXT"), ("Technology", "INT32"), ("Ignition", "BOOLEAN"),
    ("Longitude", "DOUBLE"), ("Latitude", "DOUBLE"), ("SpeedGps", "DOUBLE"),
    ("SpeedTach", "DOUBLE"), ("SpeedCan", "DOUBLE"), ("TachoGps", "DOUBLE"),
    ("TachoTach", "DOUBLE"), ("ModeDrive", "INT32"), ("SpreadingMode", "INT32"),
    ("Plow", "BOOLEAN"), ("Gram", "INT32"), ("WidthLeft", "DOUBLE"),
    ("WidthRight", "DOUBLE"), ("SumSalt", "DOUBLE"), ("SumInert", "DOUBLE"),
    ("SumBrine", "DOUBLE"), ("Cuts1", "BOOLEAN"), ("Cuts2", "BOOLEAN"),
    ("Cuts3", "BOOLEAN"), ("CentralBroom", "BOOLEAN"), ("LeftBroom", "BOOLEAN"),
    ("RightBroom", "BOOLEAN"), ("Turbine", "BOOLEAN"), ("RunningShaft", "BOOLEAN"),
    ("LeftFlushing", "BOOLEAN"), ("RightFlushing", "BOOLEAN"),
    ("CentralFlushing", "BOOLEAN"), ("Misting", "BOOLEAN"), ("Pump", "BOOLEAN"),
    ("LightOn", "BOOLEAN"), ("ModeArrow", "INT32"), ("AkuVoltage", "DOUBLE"),
    ("RampUp", "BOOLEAN"), ("Crash", "BOOLEAN"), ("TempAir", "DOUBLE"),
    ("TempRoad", "DOUBLE"), ("Revs", "DOUBLE"), ("RevsExtension", "BOOLEAN"),
    ("Fuel", "DOUBLE"), ("LevelPHM", "DOUBLE"), ("PowerVoltage", "DOUBLE"),
    ("Lighthouse", "BOOLEAN"),
]

CSV_COLS = [
    "orig_id","orig_time","orig_topic","CreatedTime","GpsTime",
    "GsmSignal","SatelliteCount","LicensePlate","VehicleType","Company",
    "VehicleID","Technology","Ignition","Longitude","Latitude",
    "SpeedGps","SpeedTach","SpeedCan","TachoGps","TachoTach",
    "ModeDrive","SpreadingMode","Plow","Gram","WidthLeft","WidthRight",
    "SumSalt","SumInert","SumBrine",
    "Cuts1","Cuts2","Cuts3","CentralBroom","LeftBroom","RightBroom",
    "Turbine","RunningShaft","LeftFlushing","RightFlushing","CentralFlushing",
    "Misting","Pump","LightOn","ModeArrow","AkuVoltage","RampUp","Crash",
    "TempAir","TempRoad","Revs","RevsExtension","Fuel","LevelPHM",
    "PowerVoltage","Lighthouse",
]

def make_record(rng: random.Random, ts: datetime, vehicle_id: str) -> dict:
    gps_time_str = ts.strftime("%Y-%m-%dT%H:%M:%S.000000")
    return {
        "orig_id":          rng.randint(1, 9_999_999),
        "orig_time":        gps_time_str,
        "orig_topic":       rng.choice(ORIG_TOPICS),
        "CreatedTime":      gps_time_str,
        "GpsTime":          ts,
        "GsmSignal":        rng.randint(0, 31),
        "SatelliteCount":   rng.randint(0, 20),
        "LicensePlate":     f"{rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{rng.randint(10,99)}{rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",
        "VehicleType":      rng.randint(1, 5),
        "Company":          rng.choice(COMPANIES),
        "VehicleID":        vehicle_id,
        "Technology":       rng.randint(0, 3),
        "Ignition":         rng.randint(0, 1),
        "Longitude":        round(rng.uniform(12.0, 18.5), 6),
        "Latitude":         round(rng.uniform(48.5, 51.5), 6),
        "SpeedGps":         round(rng.uniform(0, 130), 3),
        "SpeedTach":        round(rng.uniform(0, 130), 3),
        "SpeedCan":         round(rng.uniform(0, 130), 3),
        "TachoGps":         round(rng.uniform(0, 130), 3),
        "TachoTach":        round(rng.uniform(0, 130), 3),
        "ModeDrive":        rng.randint(0, 4),
        "SpreadingMode":    rng.randint(0, 3),
        "Plow":             rng.randint(0, 1),
        "Gram":             rng.randint(0, 500),
        "WidthLeft":        round(rng.uniform(0, 3), 3),
        "WidthRight":       round(rng.uniform(0, 3), 3),
        "SumSalt":          round(rng.uniform(0, 10000), 4),
        "SumInert":         round(rng.uniform(0, 10000), 4),
        "SumBrine":         round(rng.uniform(0, 10000), 4),
        "Cuts1":            rng.randint(0, 1),
        "Cuts2":            rng.randint(0, 1),
        "Cuts3":            rng.randint(0, 1),
        "CentralBroom":     rng.randint(0, 1),
        "LeftBroom":        rng.randint(0, 1),
        "RightBroom":       rng.randint(0, 1),
        "Turbine":          rng.randint(0, 1),
        "RunningShaft":     rng.randint(0, 1),
        "LeftFlushing":     rng.randint(0, 1),
        "RightFlushing":    rng.randint(0, 1),
        "CentralFlushing":  rng.randint(0, 1),
        "Misting":          rng.randint(0, 1),
        "Pump":             rng.randint(0, 1),
        "LightOn":          rng.randint(0, 1),
        "ModeArrow":        rng.randint(0, 5),
        "AkuVoltage":       round(rng.uniform(11.0, 14.5), 3),
        "RampUp":           rng.randint(0, 1),
        "Crash":            rng.randint(0, 1),
        "TempAir":          round(rng.uniform(-20, 40), 3),
        "TempRoad":         round(rng.uniform(-20, 40), 3),
        "Revs":             round(rng.uniform(0, 5000), 4),
        "RevsExtension":    rng.randint(0, 1),
        "Fuel":             round(rng.uniform(0, 100), 3),
        "LevelPHM":         round(rng.uniform(0, 100), 3),
        "PowerVoltage":     round(rng.uniform(11.0, 14.5), 3),
        "Lighthouse":       rng.randint(0, 1),
    }

def record_stream(
    seed: int,
    worker_id: int,
    vehicle_ids: List[str],
    base_ts: datetime,
    ts_step_ms: int,
) -> Iterator[dict]:
    """Deterministic per (seed, worker_id). O(1) memory."""
    rng = random.Random(seed ^ (worker_id * 0x9E3779B9))
    idx = 0
    while True:
        vid = vehicle_ids[idx % len(vehicle_ids)]
        offset_sec = (idx * ts_step_ms) // 1000
        offset_us  = ((idx * ts_step_ms) % 1000) * 1000
        ts = base_ts + timedelta(seconds=offset_sec, microseconds=offset_us)
        yield make_record(rng, ts, vid)
        idx += 1

class TelemetryBatchGenerator:
    """Used by benchmark harness. One batch in RAM at a time."""
    def __init__(self, seed: int, worker_id: int, vehicle_ids: List[str],
                 base_ts: datetime, ts_step_ms: int, batch_size: int):
        self._stream = record_stream(seed, worker_id, vehicle_ids, base_ts, ts_step_ms)
        self.batch_size = batch_size

    def next_batch(self) -> List[dict]:
        return [next(self._stream) for _ in range(self.batch_size)]

# formatters
def format_csv_batch(records: List[dict], include_header: bool = False) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLS, extrasaction="ignore", lineterminator="\n")
    if include_header:
        writer.writeheader()
    for r in records:
        row = r.copy()
        row["GpsTime"] = row["GpsTime"].strftime("%Y-%m-%d %H:%M:%S.%f")
        writer.writerow(row)
    return buf.getvalue()

def format_json_batch(records: List[dict]) -> str:
    lines = []
    for r in records:
        rc = r.copy()
        ts: datetime = rc["GpsTime"]
        rc["GpsTime"] = {"$date": ts.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")}
        lines.append(json.dumps(rc))
    return "\n".join(lines)

def format_line_protocol_batch(records: List[dict], table: str) -> str:
    TAG_FIELDS = {"VehicleID", "Company", "LicensePlate", "VehicleType", "Technology"}
    STRING_FIELDS = {"orig_topic", "orig_time", "CreatedTime", "GpsTime"}
    INT_FIELDS = {
        "orig_id","GsmSignal","SatelliteCount","Ignition","ModeDrive","SpreadingMode",
        "Plow","Gram","Cuts1","Cuts2","Cuts3","CentralBroom","LeftBroom","RightBroom",
        "Turbine","RunningShaft","LeftFlushing","RightFlushing","CentralFlushing",
        "Misting","Pump","LightOn","ModeArrow","RampUp","Crash","RevsExtension","Lighthouse",
    }
    def esc_tag(v):
        return str(v).replace(",", r"\,").replace("=", r"\=").replace(" ", r"\ ")
    def esc_str(v):
        return '"' + str(v).replace('"', r'\"') + '"'
    lines = []
    for r in records:
        tags = ",".join(f"{esc_tag(k)}={esc_tag(r[k])}" for k in sorted(TAG_FIELDS) if k in r)
        fields = []
        for k, v in r.items():
            if k in TAG_FIELDS or k == "GpsTime":
                continue
            if k in STRING_FIELDS:
                fields.append(f"{k}={esc_str(v)}")
            elif k in INT_FIELDS:
                fields.append(f"{k}={int(v)}i")
            else:
                fields.append(f"{k}={float(v)}")
        ts_ns = int(r["GpsTime"].timestamp() * 1_000_000_000)
        lines.append(f"{table},{tags} {','.join(fields)} {ts_ns}")
    return "\n".join(lines)

def format_questdb_batch(records: List[dict], table: str) -> str:
    TAG_FIELDS = {"VehicleID", "Company", "LicensePlate", "VehicleType", "Technology"}
    BOOL_FIELDS = {
        "Ignition","Plow","Cuts1","Cuts2","Cuts3","CentralBroom","LeftBroom","RightBroom",
        "Turbine","RunningShaft","LeftFlushing","RightFlushing","CentralFlushing",
        "Misting","Pump","LightOn","RampUp","Crash","RevsExtension","Lighthouse"
    }
    TIMESTAMP_FIELDS = {"CreatedTime", "orig_time"}
    lines = []
    for r in records:
        tags = ",".join(f"{k}={str(r[k]).replace(' ', '\\ ')}" for k in TAG_FIELDS if k in r)
        fields = []
        for k, v in r.items():
            if k in TAG_FIELDS or k == "GpsTime":
                continue
            if k in TIMESTAMP_FIELDS:
                dt = datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
                fields.append(f"{k}={int(dt.timestamp() * 1_000_000)}t")
            elif k in BOOL_FIELDS:
                fields.append(f"{k}={'true' if v else 'false'}")
            elif isinstance(v, str):
                fields.append(f'{k}="{v}"')
            elif isinstance(v, int):
                fields.append(f"{k}={v}i")
            else:
                fields.append(f"{k}={float(v)}")
        ts_ns = int(r["GpsTime"].timestamp() * 1_000_000_000)
        lines.append(f"{table},{tags} {','.join(fields)} {ts_ns}")
    return "\n".join(lines)

def format_iotdb_batch(records: List[dict], device_prefix: str) -> str:
    measurements = [m[0] for m in IOTDB_MEASUREMENTS]
    data_types   = [m[1] for m in IOTDB_MEASUREMENTS]
    devices: Dict[str, List[dict]] = {}
    for r in records:
        did = f"{device_prefix}.vehicle_{r['VehicleID']}"
        devices.setdefault(did, []).append(r)
    payloads = []
    for did, dev_records in devices.items():
        timestamps = []
        values = [[] for _ in measurements]
        for r in dev_records:
            timestamps.append(int(r["GpsTime"].timestamp() * 1000))
            for i, (field, dtype) in enumerate(IOTDB_MEASUREMENTS):
                v = r.get(field)
                if v is None:
                    values[i].append(None)
                elif dtype == "BOOLEAN":
                    values[i].append(bool(v))
                elif dtype in ("INT32", "INT64"):
                    values[i].append(int(v))
                elif dtype in ("DOUBLE", "FLOAT"):
                    values[i].append(float(v))
                else:
                    values[i].append(str(v))
        payloads.append(json.dumps({
            "deviceId": did,
            "timestamps": timestamps,
            "measurements": measurements,
            "dataTypes": data_types,
            "values": values,
            "isAligned": False,
        }))
    return "\n".join(payloads)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["csv","json","line_protocol","iotdb","questdb"], default="csv")
    ap.add_argument("--rows", type=int, default=100)
    ap.add_argument("--table", default="car_telemetry")
    ap.add_argument("--vehicle-ids", default="")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ts-start", default=None)
    ap.add_argument("--ts-step-ms", type=int, default=1000)
    ap.add_argument("--no-header", action="store_true")
    ap.add_argument("--batch-size", type=int, default=0,
                    help="If >0, emit in batches of N rows. 0=single shot.")
    args = ap.parse_args()

    vids = [v.strip() for v in args.vehicle_ids.split(",") if v.strip()] or \
           [str(random.Random(args.seed).randint(100, 999)) for _ in range(5)]

    if args.ts_start:
        base_ts = datetime.fromisoformat(args.ts_start.replace('Z', '+00:00'))
    else:
        base_ts = datetime.now(tz=timezone.utc)

    gen = record_stream(args.seed, 0, vids, base_ts, args.ts_step_ms)
    total = 0
    header_emitted = False

    while total < args.rows:
        n = min(args.batch_size or args.rows, args.rows - total)
        batch = [next(gen) for _ in range(n)]
        total += len(batch)

        if args.format == "csv":
            out = format_csv_batch(batch, include_header=(not header_emitted and not args.no_header))
            header_emitted = True
        elif args.format == "json":
            out = format_json_batch(batch)
        elif args.format == "line_protocol":
            out = format_line_protocol_batch(batch, args.table)
        elif args.format == "questdb":
            out = format_questdb_batch(batch, args.table)
        elif args.format == "iotdb":
            out = format_iotdb_batch(batch, args.table)

        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()