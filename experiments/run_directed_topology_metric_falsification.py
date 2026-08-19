from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import numpy as np

from adaptive_evolution_observer.estimator import directed_diffusivity


def _counts(n: int, edges: Iterable[tuple[int, int, float]]) -> np.ndarray:
    out = np.zeros((n, n), dtype=float)
    for i, j, w in edges:
        out[i, j] += float(w)
    return out


def branching_entropy(counts: np.ndarray) -> float | None:
    """Traffic-weighted normalized outgoing-target entropy.

    This asks whether observed interaction traffic fans out across many targets.
    It deliberately does *not* claim recurrence or fast global mixing.
    """
    n = counts.shape[0]
    total = float(counts.sum())
    if n < 2 or total <= 0:
        return None
    denom = math.log(max(2, n - 1))
    accum = 0.0
    for i in range(n):
        row_sum = float(counts[i].sum())
        if row_sum <= 0:
            continue
        p = counts[i] / row_sum
        nz = p[p > 0]
        h = -float(np.sum(nz * np.log(nz)))
        accum += (row_sum / total) * (h / denom)
    return float(np.clip(accum, 0.0, 1.0))


def reciprocity(counts: np.ndarray) -> float | None:
    """Fraction of directed traffic that has matched reverse traffic."""
    total = float(counts.sum())
    if total <= 0:
        return None
    matched = 0.0
    n = counts.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            matched += 2.0 * min(float(counts[i, j]), float(counts[j, i]))
    return float(np.clip(matched / total, 0.0, 1.0))


def _strongly_connected_components(counts: np.ndarray) -> list[list[int]]:
    adj = [list(np.flatnonzero(counts[i] > 0)) for i in range(counts.shape[0])]
    index = 0
    stack: list[int] = []
    on_stack: set[int] = set()
    indices: dict[int, int] = {}
    lowlink: dict[int, int] = {}
    result: list[list[int]] = []

    def visit(v: int) -> None:
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in adj[v]:
            if w not in indices:
                visit(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])
        if lowlink[v] == indices[v]:
            component: list[int] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                component.append(w)
                if w == v:
                    break
            result.append(sorted(component))

    for v in range(counts.shape[0]):
        if v not in indices:
            visit(v)
    return result


def recurrent_core_fraction(counts: np.ndarray) -> float | None:
    active = set(np.flatnonzero((counts.sum(axis=0) + counts.sum(axis=1)) > 0).tolist())
    if not active:
        return None
    recurrent: set[int] = set()
    for component in _strongly_connected_components(counts):
        if len(component) > 1:
            recurrent.update(component)
        elif counts[component[0], component[0]] > 0:
            recurrent.update(component)
    return len(recurrent & active) / len(active)


def recurrent_core_mixing_gap(counts: np.ndarray) -> float | None:
    """Lazy-chain spectral gap on the largest non-trivial SCC only.

    Acyclic delegation traffic has no recurrent core, so returning ``None`` is
    more honest than converting terminal leaves into absorbing self-loops and
    calling the resulting eigenvalue artifact 'diffusivity'.
    """
    components = [c for c in _strongly_connected_components(counts) if len(c) > 1]
    if not components:
        return None
    core = max(components, key=len)
    sub = counts[np.ix_(core, core)].astype(float)
    row_sum = sub.sum(axis=1)
    if np.any(row_sum <= 0):
        return None
    p = sub / row_sum[:, None]
    lazy = 0.5 * (np.eye(len(core)) + p)
    eig = np.sort(np.abs(np.linalg.eigvals(lazy)))[::-1]
    if eig.size < 2:
        return None
    return float(np.clip(1.0 - float(np.real(eig[1])), 0.0, 1.0))


def graph_library() -> dict[str, np.ndarray]:
    return {
        "star_out": _counts(5, [(0, 1, 1), (0, 2, 1), (0, 3, 1), (0, 4, 1)]),
        "chain": _counts(5, [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1)]),
        "directed_cycle": _counts(5, [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 4, 1), (4, 0, 1)]),
        "bidirectional_ring": _counts(
            5,
            [(i, (i + 1) % 5, 1) for i in range(5)]
            + [(i, (i - 1) % 5, 1) for i in range(5)],
        ),
        "complete_uniform": _counts(
            5,
            [(i, j, 1) for i in range(5) for j in range(5) if i != j],
        ),
    }


def run() -> dict:
    rows: dict[str, dict[str, float | None]] = {}
    for name, counts in graph_library().items():
        rows[name] = {
            "legacy_directed_diffusivity": directed_diffusivity(counts),
            "branching_entropy": branching_entropy(counts),
            "reciprocity": reciprocity(counts),
            "recurrent_core_fraction": recurrent_core_fraction(counts),
            "recurrent_core_mixing_gap": recurrent_core_mixing_gap(counts),
        }

    checks = {
        # The old metric calls a one-way chain maximally diffusive because all
        # traffic eventually reaches one absorbing leaf. That is the pathology
        # this experiment is intended to expose.
        "legacy_chain_exceeds_star": (
            rows["chain"]["legacy_directed_diffusivity"]
            > rows["star_out"]["legacy_directed_diffusivity"]
        ),
        "star_branches_more_than_chain": (
            rows["star_out"]["branching_entropy"]
            > rows["chain"]["branching_entropy"]
        ),
        "acyclic_graphs_have_no_recurrent_gap": (
            rows["star_out"]["recurrent_core_mixing_gap"] is None
            and rows["chain"]["recurrent_core_mixing_gap"] is None
        ),
        "recurrent_graphs_have_full_recurrent_core": all(
            rows[name]["recurrent_core_fraction"] == 1.0
            for name in ("directed_cycle", "bidirectional_ring", "complete_uniform")
        ),
        "bidirectional_ring_more_reciprocal_than_cycle": (
            rows["bidirectional_ring"]["reciprocity"]
            > rows["directed_cycle"]["reciprocity"]
        ),
        "complete_graph_branches_more_than_cycle": (
            rows["complete_uniform"]["branching_entropy"]
            > rows["directed_cycle"]["branching_entropy"]
        ),
    }
    return {
        "schema": "adaptive-evolution.directed-topology-falsification.v0.1",
        "rows": rows,
        "checks": checks,
        "passed": all(checks.values()),
        "conclusion": (
            "A single raw row-stochastic SLEM gap is not a safe Hermes delegation diffusivity metric. "
            "Separate fan-out, reciprocity/recurrent support, and recurrent-core mixing; return null when recurrence is unsupported."
        ),
        "authority": "synthetic_counterexample_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
