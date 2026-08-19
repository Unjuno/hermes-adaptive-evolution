from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Iterable

import numpy as np

from .normalizer import CanonicalEvent

ROLE_NAMES = ("research", "implementation", "verification", "coordination")


def tool_family(tool_name: str | None) -> str | None:
    if not tool_name:
        return None
    t = tool_name.lower()
    if any(k in t for k in ("search", "browser", "web", "read", "fetch", "find")):
        return "research"
    if any(k in t for k in ("test", "verify", "lint", "check")):
        return "verification"
    if any(k in t for k in ("delegate", "kanban", "task", "message", "handoff")):
        return "coordination"
    if any(k in t for k in ("terminal", "shell", "python", "write", "patch", "edit", "code")):
        return "implementation"
    return None


def _transition_matrix(counts: np.ndarray) -> np.ndarray:
    """Legacy absorbing-row transition construction.

    Retained only so falsification experiments can reproduce the original M2
    metric. It must not be used as the production organization-state signal:
    multiple terminal leaves create absorbing eigenvalues and a one-way chain
    can look maximally diffusive.
    """
    n = counts.shape[0]
    p = np.zeros_like(counts, dtype=float)
    for i in range(n):
        s = float(counts[i].sum())
        if s > 0:
            p[i] = counts[i] / s
        else:
            p[i, i] = 1.0
    return p


def directed_diffusivity(counts: np.ndarray) -> float | None:
    """Deprecated raw SLEM-gap metric, kept for explicit counterexamples only."""
    if counts.shape[0] < 2 or float(counts.sum()) <= 0:
        return None
    p = _transition_matrix(counts)
    eig = np.sort(np.abs(np.linalg.eigvals(p)))[::-1]
    if eig.size < 2:
        return None
    return float(np.clip(1.0 - float(np.real(eig[1])), 0.0, 1.0))


def interaction_branching_entropy(counts: np.ndarray) -> float | None:
    """Traffic-weighted entropy of each source's target distribution.

    Range: [0, 1]. A deterministic chain/cycle is near 0; a source spreading
    traffic uniformly across all other observed agents approaches 1. This is a
    fan-out statistic only and deliberately says nothing about recurrence.
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
        entropy = -float(np.sum(nz * np.log(nz)))
        accum += (row_sum / total) * (entropy / denom)
    return float(np.clip(accum, 0.0, 1.0))


def interaction_reciprocity(counts: np.ndarray) -> float | None:
    """Fraction of directed traffic with matched reverse traffic, in [0, 1]."""
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
    """Tarjan SCC decomposition over positive directed interaction edges."""
    adjacency = [list(np.flatnonzero(counts[i] > 0)) for i in range(counts.shape[0])]
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
        for w in adjacency[v]:
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
    """Fraction of active interaction agents that belong to a recurrent SCC."""
    active = set(np.flatnonzero((counts.sum(axis=0) + counts.sum(axis=1)) > 0).tolist())
    if not active:
        return None
    recurrent: set[int] = set()
    for component in _strongly_connected_components(counts):
        if len(component) > 1:
            recurrent.update(component)
        elif counts[component[0], component[0]] > 0:
            recurrent.update(component)
    return float(len(recurrent & active) / len(active))


def recurrent_core_mixing_gap(counts: np.ndarray) -> float | None:
    """Lazy-chain spectral gap on the largest non-trivial recurrent SCC.

    Acyclic delegation trees/DAGs have no recurrent interaction core, so this
    returns ``None`` instead of fabricating absorbing self-loops. The lazy step
    removes periodicity artifacts (for example a deterministic directed cycle)
    while preserving the recurrent support requirement.
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


def estimate(events: Iterable[CanonicalEvent]) -> dict:
    events = list(events)
    agents = sorted(
        {e.agent_id for e in events if e.agent_id}
        | {e.parent_agent_id for e in events if e.parent_agent_id}
    )
    idx = {a: i for i, a in enumerate(agents)}
    edges = np.zeros((len(agents), len(agents)), dtype=float)
    role_counts: dict[str, Counter] = defaultdict(Counter)
    successes: Counter = Counter()
    failures: Counter = Counter()

    for e in events:
        if (
            e.kind == "interaction_start"
            and e.parent_agent_id
            and e.agent_id
            and e.parent_agent_id != e.agent_id
        ):
            edges[idx[e.parent_agent_id], idx[e.agent_id]] += 1.0
            role = e.data.get("role")
            if role and role not in {"leaf", "orchestrator"}:
                role_counts[e.agent_id][str(role)] += 0.25
        elif e.kind == "tool_result" and e.agent_id:
            fam = tool_family(e.data.get("tool_name"))
            if fam:
                role_counts[e.agent_id][fam] += 1.0
            status = str(e.data.get("status") or "").lower()
            if (
                status in {"error", "failed", "blocked", "cancelled", "canceled"}
                or e.data.get("error_type")
            ):
                failures[e.agent_id] += 1
            else:
                successes[e.agent_id] += 1
        elif e.kind in {"api_error", "kanban_task_blocked"} and e.agent_id:
            failures[e.agent_id] += 1

    role_posteriors: dict[str, dict[str, float]] = {}
    role_entropy: dict[str, float] = {}
    role_confidence: dict[str, float] = {}
    role_evidence: dict[str, float] = {}
    alpha = 0.5
    for a in agents:
        evidence = float(sum(role_counts[a].values()))
        role_evidence[a] = evidence
        vec = np.array([role_counts[a][r] + alpha for r in ROLE_NAMES], dtype=float)
        p = vec / vec.sum()
        role_posteriors[a] = {r: float(v) for r, v in zip(ROLE_NAMES, p)}
        entropy = float(
            -np.sum(p * np.log(np.clip(p, 1e-12, 1.0)))
            / math.log(len(ROLE_NAMES))
        )
        role_entropy[a] = entropy
        role_confidence[a] = 0.0 if evidence <= 0 else float(np.clip(1.0 - entropy, 0.0, 1.0))

    total_edge = float(edges.sum())
    mixing = None
    role_conditioned_weight = 0.0
    mixing_numerator = 0.0
    if total_edge > 0:
        for i, ai in enumerate(agents):
            pi = np.array([role_posteriors[ai][r] for r in ROLE_NAMES])
            ci = role_confidence[ai]
            for j, aj in enumerate(agents):
                c = float(edges[i, j])
                if c <= 0:
                    continue
                cj = role_confidence[aj]
                confidence_weight = c * ci * cj
                if confidence_weight <= 0:
                    continue
                pj = np.array([role_posteriors[aj][r] for r in ROLE_NAMES])
                mixing_numerator += confidence_weight * (1.0 - float(np.dot(pi, pj)))
                role_conditioned_weight += confidence_weight
        if role_conditioned_weight > 0:
            mixing = float(mixing_numerator / role_conditioned_weight)

    role_conditioned_traffic_coverage = (
        float(role_conditioned_weight / total_edge) if total_edge > 0 else None
    )

    fragility = {}
    for a in agents:
        f = failures[a]
        s = successes[a]
        fragility[a] = float((f + 1.0) / (f + s + 2.0))

    interaction_sources = int(np.sum(edges.sum(axis=1) > 0)) if len(agents) else 0
    active_interaction_agents = int(np.sum((edges.sum(axis=0) + edges.sum(axis=1)) > 0)) if len(agents) else 0
    recurrent_fraction = recurrent_core_fraction(edges)
    recurrent_agents = (
        int(round(recurrent_fraction * active_interaction_agents))
        if recurrent_fraction is not None and active_interaction_agents
        else 0
    )

    return {
        "schema": "adaptive-evolution.organization-state.v0.3",
        "experimental": True,
        "agents": len(agents),
        "interaction_events": int(total_edge),
        "interaction_sources": interaction_sources,
        "tool_outcomes": int(sum(successes.values()) + sum(failures.values())),
        "traffic_weighted_role_mixing": mixing,
        "role_conditioned_traffic_coverage": role_conditioned_traffic_coverage,
        "interaction_branching_entropy": interaction_branching_entropy(edges),
        "interaction_reciprocity": interaction_reciprocity(edges),
        "recurrent_core_fraction": recurrent_fraction,
        "recurrent_core_mixing_gap": recurrent_core_mixing_gap(edges),
        # Diagnostic only: retained during the v0.2 -> v0.3 transition so old
        # experiment artifacts remain directly comparable. Never gate routing
        # on this field.
        "legacy_directed_diffusivity": directed_diffusivity(edges),
        "mean_role_entropy": float(np.mean(list(role_entropy.values()))) if role_entropy else None,
        "role_posteriors": role_posteriors,
        "role_confidence": role_confidence,
        "role_evidence": role_evidence,
        "fragility": fragility,
        "support": {
            "interaction_count": int(total_edge),
            "active_interaction_agents": active_interaction_agents,
            "recurrent_interaction_agents": recurrent_agents,
            "role_conditioned_interaction_weight": float(role_conditioned_weight),
            "agents_with_outgoing_interactions": interaction_sources,
            "agents_with_tool_role_evidence": sum(1 for a in agents if role_evidence[a] > 0),
            "agents_with_outcome_evidence": sum(1 for a in agents if successes[a] + failures[a] > 0),
        },
        "authority": "diagnostic_only",
        "note": (
            "Topology is decomposed into fan-out, reciprocity, recurrent support, and recurrent-core mixing. "
            "Acyclic delegation does not receive a fabricated spectral diffusivity score. Role mixing remains "
            "confidence-weighted and may be null when role evidence is insufficient. No synthetic threshold authorizes routing."
        ),
    }
