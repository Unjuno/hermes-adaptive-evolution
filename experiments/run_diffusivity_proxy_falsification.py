from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from adaptive_evolution_observer.estimator import directed_diffusivity


@dataclass
class GraphCase:
    name: str
    adjacency: np.ndarray
    directed_start_counts: np.ndarray


def _connected(adj: np.ndarray) -> bool:
    n = adj.shape[0]
    seen = {0}
    stack = [0]
    while stack:
        i = stack.pop()
        for j in np.flatnonzero(adj[i]):
            jj = int(j)
            if jj not in seen:
                seen.add(jj)
                stack.append(jj)
    return len(seen) == n


def _orient_from_root(adj: np.ndarray, root: int = 0) -> np.ndarray:
    """Orient an interaction graph into an acyclic delegation-like start graph."""
    n = adj.shape[0]
    depth = np.full(n, n + 1, dtype=int)
    depth[root] = 0
    queue = [root]
    for i in queue:
        for j in np.flatnonzero(adj[i]):
            jj = int(j)
            if depth[jj] > depth[i] + 1:
                depth[jj] = depth[i] + 1
                queue.append(jj)
    out = np.zeros_like(adj, dtype=float)
    for i in range(n):
        for j in range(i + 1, n):
            if not adj[i, j]:
                continue
            if depth[i] < depth[j]:
                out[i, j] = 1.0
            elif depth[j] < depth[i]:
                out[j, i] = 1.0
            elif i < j:
                out[i, j] = 1.0
            else:
                out[j, i] = 1.0
    return out


def completed_flow_gap(adj: np.ndarray) -> float:
    """Normalized-Laplacian algebraic connectivity of completed interactions."""
    a = np.asarray(adj, dtype=float)
    degree = a.sum(axis=1)
    if a.shape[0] < 2 or np.any(degree <= 0):
        return 0.0
    inv_sqrt = 1.0 / np.sqrt(degree)
    normalized_adj = inv_sqrt[:, None] * a * inv_sqrt[None, :]
    lap = np.eye(a.shape[0]) - normalized_adj
    eig = np.sort(np.real(np.linalg.eigvalsh(lap)))
    if eig.size < 2:
        return 0.0
    return float(np.clip(eig[1], 0.0, 2.0))


def edge_expansion_proxy(adj: np.ndarray) -> float:
    """Cheap topology proxy: harmonic mean degree normalized by n-1."""
    degree = np.asarray(adj, dtype=float).sum(axis=1)
    if np.any(degree <= 0):
        return 0.0
    harmonic = len(degree) / float(np.sum(1.0 / degree))
    return float(harmonic / max(1, len(degree) - 1))


def simulate_spread(
    adj: np.ndarray,
    *,
    infection_p: float,
    steps: int,
    replicates: int,
    rng: np.random.Generator,
) -> float:
    """Average activated fraction under a simple local SI diffusion process."""
    n = adj.shape[0]
    totals: list[float] = []
    neighbors = [np.flatnonzero(adj[i]).astype(int) for i in range(n)]
    for start in range(n):
        for _ in range(replicates):
            active = np.zeros(n, dtype=bool)
            active[start] = True
            for _step in range(steps):
                nxt = active.copy()
                for i in np.flatnonzero(active):
                    for j in neighbors[int(i)]:
                        if not nxt[j] and rng.random() < infection_p:
                            nxt[j] = True
                active = nxt
            totals.append(float(active.mean()))
    return float(np.mean(totals))


def _named_cases(n: int) -> list[GraphCase]:
    cases: list[tuple[str, np.ndarray]] = []

    path = np.zeros((n, n), dtype=float)
    for i in range(n - 1):
        path[i, i + 1] = path[i + 1, i] = 1
    cases.append(("path", path))

    star = np.zeros((n, n), dtype=float)
    for j in range(1, n):
        star[0, j] = star[j, 0] = 1
    cases.append(("star", star))

    ring = path.copy()
    ring[0, n - 1] = ring[n - 1, 0] = 1
    cases.append(("ring", ring))

    complete = np.ones((n, n), dtype=float) - np.eye(n)
    cases.append(("complete", complete))

    return [GraphCase(name, a, _orient_from_root(a)) for name, a in cases]


def build_cases(seed: int, n: int, random_cases: int) -> list[GraphCase]:
    rng = np.random.default_rng(seed)
    cases = _named_cases(n)
    attempts = 0
    while sum(c.name.startswith("random-") for c in cases) < random_cases:
        attempts += 1
        if attempts > random_cases * 100:
            raise RuntimeError("could not generate enough connected random graphs")
        p = float(rng.uniform(0.18, 0.72))
        upper = rng.random((n, n)) < p
        upper = np.triu(upper, 1)
        adj = (upper | upper.T).astype(float)
        if not _connected(adj):
            continue
        idx = sum(c.name.startswith("random-") for c in cases)
        cases.append(GraphCase(f"random-{idx:03d}", adj, _orient_from_root(adj)))
    return cases


def corr(x: list[float], y: list[float]) -> float:
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def rank_corr(x: list[float], y: list[float]) -> float:
    def ranks(v: np.ndarray) -> np.ndarray:
        order = np.argsort(v, kind="stable")
        r = np.empty(len(v), dtype=float)
        r[order] = np.arange(len(v), dtype=float)
        # Average exact ties so degenerate metrics are penalized honestly.
        for value in np.unique(v):
            mask = v == value
            if mask.sum() > 1:
                r[mask] = float(r[mask].mean())
        return r

    return corr(list(ranks(np.asarray(x, dtype=float))), list(ranks(np.asarray(y, dtype=float))))


def run(seed: int, n: int, random_cases: int, replicates: int) -> dict:
    cases = build_cases(seed, n, random_cases)
    rng = np.random.default_rng(seed + 1009)
    rows = []
    for case in cases:
        target = simulate_spread(
            case.adjacency,
            infection_p=0.25,
            steps=4,
            replicates=replicates,
            rng=rng,
        )
        current_gap = directed_diffusivity(case.directed_start_counts)
        rows.append(
            {
                "name": case.name,
                "edges": int(case.adjacency.sum() // 2),
                "spread_fraction": target,
                "current_directed_gap": None if current_gap is None else float(current_gap),
                "completed_flow_gap": completed_flow_gap(case.adjacency),
                "edge_expansion_proxy": edge_expansion_proxy(case.adjacency),
            }
        )

    target = [r["spread_fraction"] for r in rows]
    current = [0.0 if r["current_directed_gap"] is None else r["current_directed_gap"] for r in rows]
    completed = [r["completed_flow_gap"] for r in rows]
    expansion = [r["edge_expansion_proxy"] for r in rows]

    correlations = {
        "current_directed_gap": {
            "pearson": corr(current, target),
            "rank": rank_corr(current, target),
        },
        "completed_flow_gap": {
            "pearson": corr(completed, target),
            "rank": rank_corr(completed, target),
        },
        "edge_expansion_proxy": {
            "pearson": corr(expansion, target),
            "rank": rank_corr(expansion, target),
        },
    }

    named = {r["name"]: r for r in rows if not r["name"].startswith("random-")}
    conclusion = {
        "current_metric_falsified": (
            correlations["completed_flow_gap"]["rank"]
            > correlations["current_directed_gap"]["rank"] + 0.20
        ),
        "named_cases": named,
        "warning": (
            "This experiment tests topology proxies against a synthetic SI diffusion target. "
            "It does not authorize a production routing threshold."
        ),
    }
    return {
        "schema": "adaptive-evolution.diffusivity-proxy-falsification.v0.1",
        "seed": seed,
        "nodes": n,
        "random_cases": random_cases,
        "replicates_per_start": replicates,
        "target": {"process": "SI", "infection_probability": 0.25, "steps": 4},
        "correlations": correlations,
        "conclusion": conclusion,
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--nodes", type=int, default=8)
    ap.add_argument("--random-cases", type=int, default=80)
    ap.add_argument("--replicates", type=int, default=120)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = run(args.seed, args.nodes, args.random_cases, args.replicates)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
