#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_live_data import TelemetryBatchGenerator


def _load_driver(driver_path, driver_class_name):
    spec = importlib.util.spec_from_file_location("db_driver", driver_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, driver_class_name)


def _chunk_ids(all_ids: list, worker_id: int, num_workers: int) -> list:
    n = len(all_ids)
    if n < num_workers:
        raise RuntimeError(f"Need ≥{num_workers} vehicle IDs, got {n}")
    base, rem = divmod(n, num_workers)
    if worker_id < rem:
        start = worker_id * (base + 1)
        end = start + base + 1
    else:
        start = rem * (base + 1) + (worker_id - rem) * base
        end = start + base
    return all_ids[start:end]


def run_worker(worker_id, driver_path, driver_class_name, host, port, table,
                database, user, password, duration, workers, batch_size,
                seed, vehicle_ids_csv, ts_start, ts_step_ms):
    
    driver_class = _load_driver(driver_path, driver_class_name)
    driver = driver_class(host, port, table, user=user, password=password, database=database)
    driver.connect()

    all_ids = vehicle_ids_csv.split(",")
    my_ids = _chunk_ids(all_ids, worker_id, workers)

    base_ts = datetime.fromisoformat(ts_start) if ts_start else datetime.now(timezone.utc)
    gen = TelemetryBatchGenerator(
        seed=seed, 
        worker_id=worker_id,
        vehicle_ids=my_ids,
        base_ts=base_ts, 
        ts_step_ms=ts_step_ms,
        batch_size=batch_size,
    )

    total_rows = 0
    latencies = []
    errors = 0
    end = time.perf_counter() + duration

    while time.perf_counter() < end:
        batch = gen.next_batch()
        t0 = time.perf_counter()
        try:
            n_ins = driver.insert_batch(batch)
            if n_ins > 0:
                latencies.append((time.perf_counter() - t0) * 1000)
                total_rows += n_ins
        except Exception as e:
            errors += 1
            print(f"worker {worker_id} error: {e}", file=sys.stderr)

    driver.close()

    if latencies:
        s = sorted(latencies)
        p50 = s[len(s) // 2]
        p99 = s[min(int(len(s) * 0.99), len(s) - 1)]
    else:
        p50 = p99 = 0
    return {
        "worker_id": worker_id,
        "total_rows": total_rows,
        "errors": errors,
        "p50_latency_ms": round(p50, 3),
        "p99_latency_ms": round(p99, 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--driver-path", required=True)
    ap.add_argument("--driver-class", default="Driver")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--table", default="car_telemetry")
    ap.add_argument("--database", default="")
    ap.add_argument("--user", default="")
    ap.add_argument("--password", default="")
    ap.add_argument("--duration", type=int, required=True)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--batch-size", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--vehicle-ids", default="201,202,203,204,205")
    ap.add_argument("--ts-start", default=None)
    ap.add_argument("--ts-step-ms", type=int, default=1000)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    driver_class = _load_driver(args.driver_path, args.driver_class)

    setup_driver = driver_class(args.host, args.port, args.table,
                                user=args.user, password=args.password,
                                database=args.database)
    setup_driver.connect()
    setup_driver.prepare_schema()
    setup_driver.close()

    start_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    t0 = time.perf_counter()
   
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = [
            ex.submit(
                run_worker, w, args.driver_path, args.driver_class,
                args.host, args.port, args.table, args.database,
                args.user, args.password, args.duration, args.workers,
                args.batch_size, args.seed, args.vehicle_ids, args.ts_start,
                args.ts_step_ms,
            )
            for w in range(args.workers)
        ]
        results = [f.result() for f in futures]
    elapsed = time.perf_counter() - t0

    end_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total = sum(r["total_rows"] for r in results)

    report = {
        "start_datetime": start_iso,
        "end_datetime": end_iso,
        "duration_requested_sec": args.duration,
        "duration_actual_sec": round(elapsed, 3),
        "workers": args.workers,
        "batch_size": args.batch_size,
        "total_rows": total,
        "rows_per_sec": round(total / elapsed, 1) if elapsed > 0 else 0,
        "query_duration_sec": round(elapsed, 3),
        "worker_stats": [f"worker_{r['worker_id']}_rows={r['total_rows']}" for r in results],
        "worker_results": results,
    }

    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()