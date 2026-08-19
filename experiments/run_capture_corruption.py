from __future__ import annotations

import argparse
import copy
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any, Callable

from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import normalize
from adaptive_evolution_observer.store import event_key

RAW_NAME = "sanitized-raw-events.jsonl"


def load_bundle_raw(bundle: str | Path) -> list[dict[str, Any]]:
    path = Path(bundle).expanduser() / RAW_NAME
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or "hook" not in row or "payload" not in row:
            raise ValueError(f"invalid sanitized raw event at line {line_number}")
        rows.append(row)
    if not rows:
        raise ValueError("capture bundle contains no sanitized raw events")
    return rows


def _state(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    events, diagnostics = normalize(rows)
    return estimate(events), diagnostics


def _sample_count(n: int, rate: float) -> int:
    if rate <= 0:
        return 0
    return max(1, min(n, int(round(n * rate))))


def corrupt_duplicate(rows: list[dict[str, Any]], rate: float, rng: random.Random) -> list[dict[str, Any]]:
    out = copy.deepcopy(rows)
    k = _sample_count(len(rows), rate)
    for index in rng.choices(range(len(rows)), k=k):
        out.append(copy.deepcopy(rows[index]))
    rng.shuffle(out)
    return out


def corrupt_drop(rows: list[dict[str, Any]], rate: float, rng: random.Random) -> list[dict[str, Any]]:
    k = _sample_count(len(rows), rate)
    drop = set(rng.sample(range(len(rows)), k=k))
    return [copy.deepcopy(row) for i, row in enumerate(rows) if i not in drop]


def corrupt_reorder(rows: list[dict[str, Any]], rate: float, rng: random.Random) -> list[dict[str, Any]]:
    del rate
    out = copy.deepcopy(rows)
    rng.shuffle(out)
    return out


def corrupt_strip_optional_ids(rows: list[dict[str, Any]], rate: float, rng: random.Random) -> list[dict[str, Any]]:
    out = copy.deepcopy(rows)
    candidates = [i for i, row in enumerate(out) if isinstance(row.get("payload"), dict)]
    k = _sample_count(len(candidates), rate)
    for i in rng.sample(candidates, k=k):
        payload = out[i]["payload"]
        for key in ("task_id", "turn_id", "api_request_id"):
            payload.pop(key, None)
        out[i]["event_key"] = event_key(str(out[i]["hook"]), payload)
    return out


def _abs_error(a: Any, b: Any) -> float | None:
    if a is None or b is None:
        return None
    try:
        return abs(float(a) - float(b))
    except (TypeError, ValueError):
        return None


def _fragility_mae(baseline: dict[str, Any], candidate: dict[str, Any]) -> float | None:
    a = baseline.get("fragility") or {}
    b = candidate.get("fragility") or {}
    common = sorted(set(a) & set(b))
    if not common:
        return None
    return sum(abs(float(a[x]) - float(b[x])) for x in common) / len(common)


def compare_state(
    baseline: dict[str, Any], baseline_diag: dict[str, Any],
    candidate: dict[str, Any], candidate_diag: dict[str, Any],
) -> dict[str, Any]:
    baseline_unique = max(1, int(baseline_diag.get("unique_count") or 0))
    return {
        "normalized_count_ratio": float(candidate_diag.get("unique_count", 0)) / baseline_unique,
        "uncertain_session_events_delta": int(candidate_diag.get("uncertain_session_events", 0)) - int(baseline_diag.get("uncertain_session_events", 0)),
        "interaction_event_delta": int(candidate.get("interaction_events", 0)) - int(baseline.get("interaction_events", 0)),
        "completed_interaction_event_delta": int(candidate.get("completed_interaction_events", 0)) - int(baseline.get("completed_interaction_events", 0)),
        "tool_outcome_delta": int(candidate.get("tool_outcomes", 0)) - int(baseline.get("tool_outcomes", 0)),
        "role_mixing_abs_error": _abs_error(candidate.get("traffic_weighted_role_mixing"), baseline.get("traffic_weighted_role_mixing")),
        "role_conditioned_traffic_coverage_abs_error": _abs_error(candidate.get("role_conditioned_traffic_coverage"), baseline.get("role_conditioned_traffic_coverage")),
        "traffic_breadth_abs_error": _abs_error(candidate.get("directed_traffic_breadth"), baseline.get("directed_traffic_breadth")),
        "completed_flow_connectivity_abs_error": _abs_error(candidate.get("completed_flow_connectivity"), baseline.get("completed_flow_connectivity")),
        "interaction_completion_coverage_abs_error": _abs_error(candidate.get("interaction_completion_coverage"), baseline.get("interaction_completion_coverage")),
        "legacy_diffusivity_abs_error": _abs_error(candidate.get("directed_diffusivity"), baseline.get("directed_diffusivity")),
        "mean_role_entropy_abs_error": _abs_error(candidate.get("mean_role_entropy"), baseline.get("mean_role_entropy")),
        "fragility_mae": _fragility_mae(baseline, candidate),
    }


def _quantiles(values: list[float]) -> dict[str, float] | None:
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return None

    def q(p: float) -> float:
        if len(values) == 1:
            return values[0]
        pos = p * (len(values) - 1)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        if lo == hi:
            return values[lo]
        w = pos - lo
        return values[lo] * (1 - w) + values[hi] * w

    return {
        "min": values[0],
        "median": statistics.median(values),
        "p90": q(0.90),
        "max": values[-1],
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, float], list[dict[str, Any]]] = {}
    for record in records:
        groups.setdefault((record["scenario"], float(record["rate"])), []).append(record["metrics"])

    out = []
    for (scenario, rate), metrics_list in sorted(groups.items()):
        metric_names = sorted({k for metrics in metrics_list for k in metrics})
        summary = {}
        for name in metric_names:
            values = [metrics[name] for metrics in metrics_list if metrics.get(name) is not None]
            summary[name] = _quantiles(values) if values else None
        out.append({
            "scenario": scenario,
            "rate": rate,
            "replicates": len(metrics_list),
            "metrics": summary,
        })
    return {"groups": out}


def run(bundle: str | Path, *, replicates: int, seed: int) -> dict[str, Any]:
    raw = load_bundle_raw(bundle)
    baseline_state, baseline_diag = _state(raw)
    scenarios: list[tuple[str, Callable[[list[dict[str, Any]], float, random.Random], list[dict[str, Any]]], list[float]]] = [
        ("duplicate", corrupt_duplicate, [0.01, 0.05, 0.10]),
        ("drop", corrupt_drop, [0.01, 0.05, 0.10]),
        ("strip_optional_ids", corrupt_strip_optional_ids, [0.01, 0.05, 0.10]),
        ("full_reorder", corrupt_reorder, [1.0]),
    ]

    records = []
    master = random.Random(seed)
    for scenario, fn, rates in scenarios:
        for rate in rates:
            for replicate in range(replicates):
                rng = random.Random(master.getrandbits(64))
                corrupted = fn(raw, rate, rng)
                candidate_state, candidate_diag = _state(corrupted)
                records.append({
                    "scenario": scenario,
                    "rate": rate,
                    "replicate": replicate,
                    "metrics": compare_state(
                        baseline_state, baseline_diag, candidate_state, candidate_diag
                    ),
                })

    return {
        "schema": "adaptive-evolution.capture-corruption.v0.2",
        "bundle": str(Path(bundle).expanduser()),
        "seed": seed,
        "replicates": replicates,
        "baseline": {
            "event_diagnostics": baseline_diag,
            "organization_state": baseline_state,
        },
        "summary": summarize(records),
        "records": records,
        "authority": "experiment_only",
        "note": (
            "No corruption-rate or sample-count result is a production activation threshold. "
            "Topology corruption is evaluated as a vector: traffic breadth, completed-flow connectivity, "
            "and completion support are separate observables."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run E2 corruption/replay experiments on a capture bundle.")
    parser.add_argument("bundle", help="Capture bundle directory created by adaptive-evolution-observer bundle")
    parser.add_argument("--replicates", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260819)
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args(argv)
    if args.replicates < 1:
        raise SystemExit("--replicates must be >= 1")
    result = run(args.bundle, replicates=args.replicates, seed=args.seed)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
