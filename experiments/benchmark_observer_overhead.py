from __future__ import annotations

import argparse
import json
import math
import platform
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import normalize
from adaptive_evolution_observer.store import EventStore


def _quantile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = p * (len(ordered) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    weight = pos - lo
    return ordered[lo] * (1 - weight) + ordered[hi] * weight


def _latency_summary(values_us: list[float]) -> dict[str, float]:
    return {
        "median_us": statistics.median(values_us),
        "p95_us": _quantile(values_us, 0.95),
        "p99_us": _quantile(values_us, 0.99),
        "max_us": max(values_us),
    }


def benchmark(events: int, payload_bytes: int, warmup: int) -> dict[str, Any]:
    if events < 1:
        raise ValueError("events must be >= 1")
    if payload_bytes < 0:
        raise ValueError("payload_bytes must be >= 0")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    with tempfile.TemporaryDirectory(prefix="adaptive-evolution-overhead-") as td:
        store = EventStore(Path(td) / "observer.sqlite3")
        content = "x" * payload_bytes

        def append_one(i: int) -> None:
            store.append("post_tool_call", {
                "session_id": "benchmark-session",
                "task_id": "benchmark-task",
                "turn_id": f"turn-{i}",
                "tool_call_id": f"tool-{i}",
                "tool_name": "python",
                "args": {"code": content, "api_key": "redacted-fixture"},
                "result": content,
                "status": "success",
                "duration_ms": 1,
            })

        for i in range(warmup):
            append_one(-i - 1)

        latencies_us = []
        started = time.perf_counter_ns()
        for i in range(events):
            t0 = time.perf_counter_ns()
            append_one(i)
            latencies_us.append((time.perf_counter_ns() - t0) / 1_000.0)
        write_total_ns = time.perf_counter_ns() - started

        raw = store.load(limit=events)
        t0 = time.perf_counter_ns()
        canonical, diagnostics = normalize(raw)
        normalize_ns = time.perf_counter_ns() - t0

        t0 = time.perf_counter_ns()
        state = estimate(canonical)
        estimate_ns = time.perf_counter_ns() - t0

        return {
            "schema": "adaptive-evolution.observer-overhead.v0.1",
            "configuration": {
                "measured_events": events,
                "warmup_events": warmup,
                "synthetic_content_bytes_per_tool_arg_and_result": payload_bytes,
                "capture_content_enabled": False,
            },
            "write": {
                **_latency_summary(latencies_us),
                "total_ms": write_total_ns / 1_000_000.0,
                "throughput_events_per_s": events / (write_total_ns / 1_000_000_000.0),
            },
            "replay": {
                "normalize_total_ms": normalize_ns / 1_000_000.0,
                "normalize_us_per_event": normalize_ns / 1_000.0 / max(1, len(raw)),
                "estimate_total_ms": estimate_ns / 1_000_000.0,
                "estimate_us_per_event": estimate_ns / 1_000.0 / max(1, len(canonical)),
                "event_diagnostics": diagnostics,
                "organization_state_schema": state.get("schema"),
            },
            "environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "sqlite": sqlite3.sqlite_version,
            },
            "authority": "benchmark_only",
            "note": "This isolates observer storage/replay cost; it is not end-to-end Hermes overhead and defines no production threshold.",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark isolated observer write and replay overhead.")
    parser.add_argument("--events", type=int, default=1000)
    parser.add_argument("--payload-bytes", type=int, default=1024)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    result = benchmark(args.events, args.payload_bytes, args.warmup)
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
