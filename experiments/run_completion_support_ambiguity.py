from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from adaptive_evolution_observer.estimator import (
    completed_flow_connectivity,
    interaction_completion_coverage,
)
from run_diffusivity_proxy_falsification import _orient_from_root


def bridge_graph() -> tuple[np.ndarray, tuple[int, int], tuple[int, int]]:
    """Two dense groups with two cross bridges; return one bridge and one local edge."""
    n = 10
    a = np.zeros((n, n), dtype=float)
    for group in (range(0, 5), range(5, 10)):
        g = list(group)
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a[g[i], g[j]] = a[g[j], g[i]] = 1.0
    for u, v in ((0, 5), (1, 6)):
        a[u, v] = a[v, u] = 1.0
    return a, (0, 5), (2, 3)


def remove_stop_for_undirected_edge(starts: np.ndarray, stops: np.ndarray, edge: tuple[int, int]) -> None:
    u, v = edge
    if starts[u, v] > 0:
        stops[u, v] = 0.0
    elif starts[v, u] > 0:
        stops[v, u] = 0.0
    else:
        raise ValueError(f"edge {edge} not present in oriented starts")


def run() -> dict:
    adj, bridge, local = bridge_graph()
    starts = _orient_from_root(adj)
    baseline_stops = starts.copy()
    baseline = completed_flow_connectivity(starts, baseline_stops)

    scenarios = []
    for name, edge in (("missing_bridge_return", bridge), ("missing_local_return", local)):
        stops = baseline_stops.copy()
        remove_stop_for_undirected_edge(starts, stops, edge)
        conn = completed_flow_connectivity(starts, stops)
        coverage = interaction_completion_coverage(starts, stops)
        scenarios.append({
            "scenario": name,
            "missing_edge": list(edge),
            "completion_coverage": coverage,
            "completed_flow_connectivity": conn,
            "absolute_connectivity_error": None if baseline is None or conn is None else abs(baseline - conn),
        })

    same_coverage = abs(float(scenarios[0]["completion_coverage"]) - float(scenarios[1]["completion_coverage"])) < 1e-12
    errors = [float(s["absolute_connectivity_error"]) for s in scenarios]
    error_ratio = max(errors) / max(min(errors), 1e-12)
    return {
        "schema": "adaptive-evolution.completion-support-ambiguity.v0.1",
        "baseline": {
            "started_relations": int(starts.sum()),
            "completed_flow_connectivity": baseline,
            "completion_coverage": interaction_completion_coverage(starts, baseline_stops),
        },
        "scenarios": scenarios,
        "conclusion": {
            "same_completion_coverage": same_coverage,
            "connectivity_error_ratio": error_ratio,
            "coverage_alone_falsified_as_confidence": bool(same_coverage and error_ratio > 2.0),
            "implication": (
                "Completion coverage is support metadata, not a calibrated confidence score. "
                "Which relation is missing matters; routing gates must keep topology value and support separate."
            ),
        },
        "authority": "synthetic_support_falsification_only",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
