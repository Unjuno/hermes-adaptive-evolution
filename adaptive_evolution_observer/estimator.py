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
    if counts.shape[0] < 2 or float(counts.sum()) <= 0:
        return None
    p = _transition_matrix(counts)
    eig = np.sort(np.abs(np.linalg.eigvals(p)))[::-1]
    if eig.size < 2:
        return None
    return float(np.clip(1.0 - float(np.real(eig[1])), 0.0, 1.0))


def estimate(events: Iterable[CanonicalEvent]) -> dict:
    events = list(events)
    agents = sorted({e.agent_id for e in events if e.agent_id} | {e.parent_agent_id for e in events if e.parent_agent_id})
    idx = {a: i for i, a in enumerate(agents)}
    edges = np.zeros((len(agents), len(agents)), dtype=float)
    role_counts: dict[str, Counter] = defaultdict(Counter)
    successes: Counter = Counter()
    failures: Counter = Counter()

    for e in events:
        if e.kind == "interaction_start" and e.parent_agent_id and e.agent_id and e.parent_agent_id != e.agent_id:
            edges[idx[e.parent_agent_id], idx[e.agent_id]] += 1.0
            role = e.data.get("role")
            if role and role not in {"leaf", "orchestrator"}:
                role_counts[e.agent_id][str(role)] += 0.25
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
    alpha = 0.5
    for a in agents:
        vec = np.array([role_counts[a][r] + alpha for r in ROLE_NAMES], dtype=float)
        p = vec / vec.sum()
        role_posteriors[a] = {r: float(v) for r, v in zip(ROLE_NAMES, p)}
        role_entropy[a] = float(-np.sum(p * np.log(np.clip(p, 1e-12, 1.0))) / math.log(len(ROLE_NAMES)))

    total_edge = float(edges.sum())
    mixing = None
    if total_edge > 0:
        cross = 0.0
        for i, ai in enumerate(agents):
            pi = np.array([role_posteriors[ai][r] for r in ROLE_NAMES])
            for j, aj in enumerate(agents):
                c = edges[i, j]
                if c <= 0:
                    continue
                pj = np.array([role_posteriors[aj][r] for r in ROLE_NAMES])
                cross += c * (1.0 - float(np.dot(pi, pj)))
        mixing = float(cross / total_edge)

    fragility = {}
    for a in agents:
        f = failures[a]
        s = successes[a]
        fragility[a] = float((f + 1.0) / (f + s + 2.0))

    interaction_sources = int(np.sum(edges.sum(axis=1) > 0)) if len(agents) else 0
    return {
        "schema": "adaptive-evolution.organization-state.v0.1",
        "experimental": True,
        "agents": len(agents),
        "interaction_events": int(total_edge),
        "interaction_sources": interaction_sources,
        "tool_outcomes": int(sum(successes.values()) + sum(failures.values())),
        "traffic_weighted_role_mixing": mixing,
        "directed_diffusivity": directed_diffusivity(edges),
        "mean_role_entropy": float(np.mean(list(role_entropy.values()))) if role_entropy else None,
        "role_posteriors": role_posteriors,
        "fragility": fragility,
        "support": {
            "interaction_count": int(total_edge),
            "agents_with_outgoing_interactions": interaction_sources,
            "agents_with_tool_role_evidence": sum(1 for a in agents if sum(role_counts[a].values()) > 0),
            "agents_with_outcome_evidence": sum(1 for a in agents if successes[a] + failures[a] > 0),
        },
        "authority": "diagnostic_only",
        "note": "No synthetic event-count threshold authorizes routing; calibrate gates on real Hermes tasks.",
    }
