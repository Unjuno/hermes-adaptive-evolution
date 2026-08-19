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
    """Legacy start-only SLEM gap; diagnostic only."""
    if counts.shape[0] < 2 or float(counts.sum()) <= 0:
        return None
    p = _transition_matrix(counts)
    eig = np.sort(np.abs(np.linalg.eigvals(p)))[::-1]
    if eig.size < 2:
        return None
    return float(np.clip(1.0 - float(np.real(eig[1])), 0.0, 1.0))


def directed_traffic_breadth(counts: np.ndarray) -> float | None:
    """Traffic-weighted effective outgoing breadth in [0, 1]."""
    counts = np.asarray(counts, dtype=float)
    total = float(counts.sum())
    if counts.shape[0] < 2 or total <= 0:
        return None
    active = (counts.sum(axis=0) + counts.sum(axis=1)) > 0
    active_n = int(active.sum())
    if active_n < 2:
        return None
    denom = float(max(1, active_n - 1))
    weighted = 0.0
    weight_sum = 0.0
    for i in np.flatnonzero(counts.sum(axis=1) > 0):
        row = counts[int(i)]
        row_sum = float(row.sum())
        p = row[row > 0] / row_sum
        entropy = -float(np.sum(p * np.log(p))) if p.size else 0.0
        effective_children = math.exp(entropy)
        breadth = float(np.clip(effective_children / denom, 0.0, 1.0))
        weighted += row_sum * breadth
        weight_sum += row_sum
    return float(weighted / weight_sum) if weight_sum > 0 else None


def _completed_counts(starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    return np.minimum(np.asarray(starts, dtype=float), np.asarray(stops, dtype=float))


def interaction_completion_coverage(starts: np.ndarray, stops: np.ndarray) -> float | None:
    start_total = float(np.asarray(starts, dtype=float).sum())
    if start_total <= 0:
        return None
    completed = float(_completed_counts(starts, stops).sum())
    return float(np.clip(completed / start_total, 0.0, 1.0))


def completed_flow_connectivity(starts: np.ndarray, stops: np.ndarray) -> float | None:
    """Monotone global connectivity of completed interaction relations.

    `None` means there is no completed relation evidence at all. Once at least
    one completion exists, the node set is defined by *start* evidence so a
    started child with a missing stop remains an isolate and can drive the
    connectivity estimate to zero rather than disappearing from the graph.

    Completed relations are binarized and symmetrized. The metric is
    lambda_2(L) / N for the unnormalized graph Laplacian L. For a fixed node
    set, adding a non-negative edge Laplacian cannot decrease lambda_2, so more
    completed relation evidence cannot spuriously make connectivity worse. A
    complete graph maps to 1.
    """
    starts = np.asarray(starts, dtype=float)
    completed = _completed_counts(starts, stops)
    if float(completed.sum()) <= 0:
        return None
    start_active = (starts.sum(axis=0) + starts.sum(axis=1)) > 0
    n = int(start_active.sum())
    if n < 2:
        return None
    sym = ((completed + completed.T) > 0).astype(float)
    a = sym[np.ix_(start_active, start_active)]
    degree = a.sum(axis=1)
    if np.any(degree <= 0):
        return 0.0
    lap = np.diag(degree) - a
    eig = np.sort(np.real(np.linalg.eigvalsh(lap)))
    if eig.size < 2:
        return None
    return float(np.clip(eig[1] / n, 0.0, 1.0))


def estimate(events: Iterable[CanonicalEvent]) -> dict:
    events = list(events)
    agents = sorted(
        {e.agent_id for e in events if e.agent_id}
        | {e.parent_agent_id for e in events if e.parent_agent_id}
    )
    idx = {a: i for i, a in enumerate(agents)}
    start_edges = np.zeros((len(agents), len(agents)), dtype=float)
    stop_edges = np.zeros((len(agents), len(agents)), dtype=float)
    role_counts: dict[str, Counter] = defaultdict(Counter)
    successes: Counter = Counter()
    failures: Counter = Counter()

    for e in events:
        if e.kind == "interaction_start" and e.parent_agent_id and e.agent_id and e.parent_agent_id != e.agent_id:
            start_edges[idx[e.parent_agent_id], idx[e.agent_id]] += 1.0
            role = e.data.get("role")
            if role and role not in {"leaf", "orchestrator"}:
                role_counts[e.agent_id][str(role)] += 0.25
        elif e.kind == "interaction_stop" and e.parent_agent_id and e.agent_id and e.parent_agent_id != e.agent_id:
            stop_edges[idx[e.parent_agent_id], idx[e.agent_id]] += 1.0
        elif e.kind == "tool_result" and e.agent_id:
            fam = tool_family(e.data.get("tool_name"))
            if fam:
                role_counts[e.agent_id][fam] += 1.0
            status = str(e.data.get("status") or "").lower()
            if status in {"error", "failed", "blocked", "cancelled", "canceled"} or e.data.get("error_type"):
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
        entropy = float(-np.sum(p * np.log(np.clip(p, 1e-12, 1.0))) / math.log(len(ROLE_NAMES)))
        role_entropy[a] = entropy
        role_confidence[a] = 0.0 if evidence <= 0 else float(np.clip(1.0 - entropy, 0.0, 1.0))

    total_edge = float(start_edges.sum())
    mixing = None
    role_conditioned_weight = 0.0
    mixing_numerator = 0.0
    if total_edge > 0:
        for i, ai in enumerate(agents):
            pi = np.array([role_posteriors[ai][r] for r in ROLE_NAMES])
            ci = role_confidence[ai]
            for j, aj in enumerate(agents):
                c = float(start_edges[i, j])
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

    role_conditioned_traffic_coverage = float(role_conditioned_weight / total_edge) if total_edge > 0 else None

    fragility = {}
    for a in agents:
        f = failures[a]
        s = successes[a]
        fragility[a] = float((f + 1.0) / (f + s + 2.0))

    interaction_sources = int(np.sum(start_edges.sum(axis=1) > 0)) if len(agents) else 0
    completed_edges = _completed_counts(start_edges, stop_edges)
    completed_count = int(completed_edges.sum())
    completion_coverage = interaction_completion_coverage(start_edges, stop_edges)
    legacy_gap = directed_diffusivity(start_edges)
    return {
        "schema": "adaptive-evolution.organization-state.v0.4",
        "experimental": True,
        "agents": len(agents),
        "interaction_events": int(total_edge),
        "completed_interaction_events": completed_count,
        "interaction_sources": interaction_sources,
        "tool_outcomes": int(sum(successes.values()) + sum(failures.values())),
        "traffic_weighted_role_mixing": mixing,
        "role_conditioned_traffic_coverage": role_conditioned_traffic_coverage,
        "directed_traffic_breadth": directed_traffic_breadth(start_edges),
        "completed_flow_connectivity": completed_flow_connectivity(start_edges, stop_edges),
        "completed_flow_connectivity_method": "unnormalized_algebraic_lambda2_over_n_binary_completed_relations",
        "interaction_completion_coverage": completion_coverage,
        "directed_diffusivity": legacy_gap,
        "directed_diffusivity_authority": "deprecated_diagnostic_only",
        "mean_role_entropy": float(np.mean(list(role_entropy.values()))) if role_entropy else None,
        "role_posteriors": role_posteriors,
        "role_confidence": role_confidence,
        "role_evidence": role_evidence,
        "fragility": fragility,
        "support": {
            "interaction_count": int(total_edge),
            "completed_interaction_count": completed_count,
            "interaction_completion_coverage": completion_coverage,
            "role_conditioned_interaction_weight": float(role_conditioned_weight),
            "agents_with_outgoing_interactions": interaction_sources,
            "agents_with_tool_role_evidence": sum(1 for a in agents if role_evidence[a] > 0),
            "agents_with_outcome_evidence": sum(1 for a in agents if successes[a] + failures[a] > 0),
        },
        "authority": "diagnostic_only",
        "note": (
            "Topology is intentionally vector-valued: directed traffic breadth measures local fan-out, while "
            "completed-flow connectivity measures global bottlenecks. v0.4 uses monotone unnormalized algebraic "
            "connectivity on binary completed relations so additional completed-edge evidence cannot worsen the "
            "connectivity value for a fixed node set. Completion coverage remains support metadata, not confidence. "
            "The legacy start-only directed_diffusivity is retained only for backward-compatible diagnostics. "
            "No synthetic event-count threshold authorizes routing; calibrate gates on real Hermes tasks."
        ),
    }
