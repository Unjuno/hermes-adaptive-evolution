from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from run_diffusivity_proxy_falsification import (
    completed_flow_gap,
    edge_expansion_proxy,
    _orient_from_root,
)
from adaptive_evolution_observer.estimator import directed_diffusivity


def two_clique_bridge_case(swaps: int) -> np.ndarray:
    """8-node 3-regular graphs with identical degree and different bottlenecks."""
    n = 8
    a = np.zeros((n, n), dtype=float)
    for group in (range(0, 4), range(4, 8)):
        g = list(group)
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                a[g[i], g[j]] = a[g[j], g[i]] = 1.0

    swaps_to_apply = [
        ((0, 1), (4, 5), (0, 4), (1, 5)),
        ((2, 3), (6, 7), (2, 6), (3, 7)),
    ]
    for idx in range(swaps):
        e1, e2, c1, c2 = swaps_to_apply[idx]
        for u, v in (e1, e2):
            a[u, v] = a[v, u] = 0.0
        for u, v in (c1, c2):
            a[u, v] = a[v, u] = 1.0
    return a


def cube_graph() -> np.ndarray:
    a = np.zeros((8, 8), dtype=float)
    for i in range(8):
        for bit in (1, 2, 4):
            j = i ^ bit
            a[i, j] = a[j, i] = 1.0
    return a


def lazy_matrix(adj: np.ndarray) -> np.ndarray:
    deg = adj.sum(axis=1)
    p = adj / deg[:, None]
    return 0.5 * np.eye(len(adj)) + 0.5 * p


def cross_partition_reach(
    adj: np.ndarray,
    *,
    steps: int,
    infection_p: float,
    replicates: int,
    rng: np.random.Generator,
) -> float:
    neighbors = [np.flatnonzero(adj[i]).astype(int) for i in range(len(adj))]
    hits = 0
    total = 0
    for start in range(4):
        for _ in range(replicates):
            active = np.zeros(len(adj), dtype=bool)
            active[start] = True
            for _step in range(steps):
                nxt = active.copy()
                for i in np.flatnonzero(active):
                    for j in neighbors[int(i)]:
                        if not nxt[j] and rng.random() < infection_p:
                            nxt[j] = True
                active = nxt
            hits += int(bool(active[4:].any()))
            total += 1
    return hits / total


def consensus_residual(adj: np.ndarray, *, steps: int, rng: np.random.Generator, reps: int) -> float:
    p = lazy_matrix(adj)
    vals = []
    for _ in range(reps):
        x = rng.normal(size=len(adj))
        x -= x.mean()
        initial = float(np.mean(x * x))
        for _step in range(steps):
            x = p @ x
        residual = float(np.mean(x * x)) / max(initial, 1e-12)
        vals.append(residual)
    return float(np.mean(vals))


def metrics(adj: np.ndarray) -> dict:
    current = directed_diffusivity(_orient_from_root(adj))
    return {
        "current_directed_gap": None if current is None else float(current),
        "completed_flow_gap": completed_flow_gap(adj),
        "edge_expansion_proxy": edge_expansion_proxy(adj),
        "degree_sequence": [int(x) for x in adj.sum(axis=1)],
    }


def run(seed: int, replicates: int) -> dict:
    rng = np.random.default_rng(seed)
    cases = {
        "two_cliques_two_bridges": two_clique_bridge_case(1),
        "two_cliques_four_bridges": two_clique_bridge_case(2),
        "cube": cube_graph(),
    }
    rows = []
    for name, adj in cases.items():
        m = metrics(adj)
        rows.append({
            "name": name,
            **m,
            "cross_partition_reach": cross_partition_reach(
                adj, steps=4, infection_p=0.25, replicates=replicates, rng=rng
            ),
            "consensus_residual": consensus_residual(adj, steps=6, rng=rng, reps=replicates),
        })

    expansion_values = [r["edge_expansion_proxy"] for r in rows]
    expansion_blind = max(expansion_values) - min(expansion_values) < 1e-12
    connectivity_values = [r["completed_flow_gap"] for r in rows]
    reach_values = [r["cross_partition_reach"] for r in rows]
    consensus_values = [r["consensus_residual"] for r in rows]

    connectivity_tracks_reach = np.corrcoef(connectivity_values, reach_values)[0, 1]
    connectivity_tracks_consensus = np.corrcoef(connectivity_values, [-x for x in consensus_values])[0, 1]

    return {
        "schema": "adaptive-evolution.topology-proxy-multitarget.v0.1",
        "seed": seed,
        "replicates": replicates,
        "rows": rows,
        "conclusion": {
            "degree_proxy_blind_by_construction": bool(expansion_blind),
            "completed_flow_gap_vs_cross_reach_corr": float(connectivity_tracks_reach),
            "completed_flow_gap_vs_consensus_speed_corr": float(connectivity_tracks_consensus),
            "retain_vector_state": bool(
                expansion_blind
                and connectivity_tracks_reach > 0.5
                and connectivity_tracks_consensus > 0.5
            ),
            "recommended_topology_state": [
                "traffic/local breadth",
                "completed-flow/global connectivity",
            ],
            "note": (
                "Equal-degree cases deliberately falsify any policy that collapses topology to degree/breadth alone. "
                "No synthetic metric is a production routing threshold."
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=23)
    ap.add_argument("--replicates", type=int, default=3000)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = run(args.seed, args.replicates)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
