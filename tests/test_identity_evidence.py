from __future__ import annotations

from adaptive_evolution_observer.normalizer import normalize


def test_session_start_without_platform_is_not_root_evidence():
    rows = [
        {
            "received_at_ns": 1,
            "hook": "on_session_start",
            "event_key": "start",
            "payload": {"session_id": "session-a"},
        },
        {
            "received_at_ns": 2,
            "hook": "post_tool_call",
            "event_key": "tool",
            "payload": {
                "session_id": "session-a",
                "turn_id": "t1",
                "tool_call_id": "tc1",
                "tool_name": "python",
                "status": "success",
            },
        },
    ]
    events, diag = normalize(rows)
    assert diag["known_root_sessions"] == 0
    assert diag["uncertain_session_events"] >= 2
    assert {e.agent_id for e in events} == {"session:session-a"}


def test_delegation_parent_establishes_root_even_without_session_platform():
    rows = [
        {
            "received_at_ns": 1,
            "hook": "on_session_start",
            "event_key": "start",
            "payload": {"session_id": "session-a"},
        },
        {
            "received_at_ns": 2,
            "hook": "subagent_start",
            "event_key": "child-start",
            "payload": {
                "parent_session_id": "session-a",
                "parent_turn_id": "t1",
                "child_session_id": "child",
                "child_subagent_id": "sub1",
                "child_role": "leaf",
            },
        },
        {
            "received_at_ns": 3,
            "hook": "post_tool_call",
            "event_key": "root-tool",
            "payload": {
                "session_id": "session-a",
                "turn_id": "t2",
                "tool_call_id": "tc2",
                "tool_name": "python",
                "status": "success",
            },
        },
    ]
    events, diag = normalize(rows)
    root_tool = next(e for e in events if e.kind == "tool_result")
    assert root_tool.agent_id == "root:session-a"
    assert diag["known_root_sessions"] == 1
