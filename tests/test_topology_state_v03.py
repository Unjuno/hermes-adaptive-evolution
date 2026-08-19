from __future__ import annotations

from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import CanonicalEvent


def _event(seq: int, kind: str, *, agent: str, parent: str | None = None) -> CanonicalEvent:
    return CanonicalEvent(
        seq=seq,
        observed_at_ns=seq,
        hook="subagent_start" if kind == "interaction_start" else "subagent_stop",
        event_key=f"e{seq}",
        session_id=f"s-{agent}",
        task_id="t",
        turn_id="turn",
        agent_id=agent,
        parent_agent_id=parent,
        kind=kind,
        data={},
    )


def test_completed_connectivity_requires_return_evidence():
    events = [_event(1, "interaction_start", agent="child", parent="root")]
    state = estimate(events)
    assert state["schema"] == "adaptive-evolution.organization-state.v0.3"
    assert state["interaction_events"] == 1
    assert state["completed_interaction_events"] == 0
    assert state["interaction_completion_coverage"] == 0.0
    assert state["completed_flow_connectivity"] is None
    assert state["directed_diffusivity_authority"] == "deprecated_diagnostic_only"


def test_one_completed_relation_has_full_completion_support():
    events = [
        _event(1, "interaction_start", agent="child", parent="root"),
        _event(2, "interaction_stop", agent="child", parent="root"),
    ]
    state = estimate(events)
    assert state["completed_interaction_events"] == 1
    assert state["interaction_completion_coverage"] == 1.0
    assert state["directed_traffic_breadth"] == 1.0
    assert state["completed_flow_connectivity"] == 1.0


def _topology(edges: list[tuple[str, str]]):
    events = []
    seq = 1
    for parent, child in edges:
        events.append(_event(seq, "interaction_start", agent=child, parent=parent))
        seq += 1
        events.append(_event(seq, "interaction_stop", agent=child, parent=parent))
        seq += 1
    return estimate(events)


def test_breadth_and_global_connectivity_are_distinct_observables():
    star = _topology([("root", "a"), ("root", "b"), ("root", "c")])
    chain = _topology([("root", "a"), ("a", "b"), ("b", "c")])

    assert star["interaction_completion_coverage"] == 1.0
    assert chain["interaction_completion_coverage"] == 1.0
    assert star["directed_traffic_breadth"] > chain["directed_traffic_breadth"]
    assert star["completed_flow_connectivity"] is not None
    assert chain["completed_flow_connectivity"] is not None
    # Neither quantity is a synonym for the legacy start-only SLEM gap.
    assert "directed_diffusivity" in star
    assert star["directed_diffusivity_authority"] == "deprecated_diagnostic_only"


def test_missing_one_stop_reduces_completion_coverage():
    events = [
        _event(1, "interaction_start", agent="a", parent="root"),
        _event(2, "interaction_stop", agent="a", parent="root"),
        _event(3, "interaction_start", agent="b", parent="root"),
    ]
    state = estimate(events)
    assert state["interaction_events"] == 2
    assert state["completed_interaction_events"] == 1
    assert state["interaction_completion_coverage"] == 0.5
