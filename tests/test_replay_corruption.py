from __future__ import annotations

import copy
import random

from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import normalize


def _base_rows():
    return [
        {"id": 1, "received_at_ns": 1, "hook": "on_session_start", "event_key": "session-root", "payload": {"session_id": "root"}},
        {"id": 2, "received_at_ns": 2, "hook": "subagent_start", "event_key": "start-child", "payload": {
            "parent_session_id": "root", "parent_turn_id": "pt1",
            "child_session_id": "child", "child_subagent_id": "sub1", "child_role": "leaf",
        }},
        {"id": 3, "received_at_ns": 3, "hook": "post_tool_call", "event_key": "tool-search", "payload": {
            "session_id": "child", "task_id": "task-child", "turn_id": "ct1",
            "tool_call_id": "tc1", "tool_name": "web_search", "status": "success",
        }},
        {"id": 4, "received_at_ns": 4, "hook": "api_request_error", "event_key": "api-error", "payload": {
            "session_id": "child", "task_id": "task-child", "turn_id": "ct2",
            "api_request_id": "api1", "status_code": 500, "retry_count": 1,
            "retryable": True, "reason": "upstream failure",
        }},
        {"id": 5, "received_at_ns": 5, "hook": "post_tool_call", "event_key": "tool-recovery", "payload": {
            "session_id": "child", "task_id": "task-child", "turn_id": "ct3",
            "tool_call_id": "tc2", "tool_name": "python", "status": "success",
        }},
        {"id": 6, "received_at_ns": 6, "hook": "subagent_stop", "event_key": "stop-child", "payload": {
            "parent_session_id": "root", "parent_turn_id": "pt1",
            "child_session_id": "child", "child_role": "leaf",
            "child_status": "completed", "duration_ms": 25,
        }},
        {"id": 7, "received_at_ns": 7, "hook": "on_session_end", "event_key": "session-end", "payload": {
            "session_id": "root", "task_id": "task-root", "turn_id": "pt1", "completed": True,
        }},
    ]


def _semantic_projection(events):
    return sorted(
        (
            e.event_key,
            e.hook,
            e.session_id,
            e.agent_id,
            e.parent_agent_id,
            e.kind,
        )
        for e in events
    )


def test_duplicate_and_full_reorder_preserve_semantics():
    baseline, baseline_diag = normalize(_base_rows())
    rows = copy.deepcopy(_base_rows())
    rows.extend(copy.deepcopy(row) for row in (_base_rows()[1], _base_rows()[2], _base_rows()[5]))
    random.Random(47).shuffle(rows)

    replay, diag = normalize(rows)
    assert _semantic_projection(replay) == _semantic_projection(baseline)
    assert diag["duplicates_removed"] == 3
    assert diag["uncertain_session_events"] == 0
    assert baseline_diag["uncertain_session_events"] == 0
    assert estimate(replay)["interaction_events"] == estimate(baseline)["interaction_events"] == 1


def test_optional_correlation_loss_fails_soft_when_session_identity_survives():
    rows = copy.deepcopy(_base_rows())
    for row in rows:
        if row["hook"] in {"post_tool_call", "api_request_error"}:
            row["payload"].pop("task_id", None)
            row["payload"].pop("turn_id", None)
            row["payload"].pop("api_request_id", None)

    events, diag = normalize(rows)
    child_observations = [e for e in events if e.kind in {"tool_result", "api_error"}]
    assert child_observations
    assert all(e.agent_id == "subagent:sub1" for e in child_observations)
    assert diag["uncertain_session_events"] == 0


def test_missing_child_start_creates_uncertainty_not_a_phantom_root():
    rows = [row for row in copy.deepcopy(_base_rows()) if row["hook"] != "subagent_start"]
    events, diag = normalize(rows)
    child_observations = [e for e in events if e.session_id == "child"]
    assert child_observations
    assert all(e.agent_id == "session:child" for e in child_observations)
    assert all(e.agent_id != "root:child" for e in child_observations)
    assert diag["uncertain_session_events"] >= 1
    assert estimate(events)["interaction_events"] == 0
