from __future__ import annotations

from pathlib import Path

from adaptive_evolution_observer.bundle import create_bundle
from adaptive_evolution_observer.store import EventStore
from experiments.validate_e1_capture import validate


def _capture(
    tmp_path: Path,
    *,
    include_recovery: bool = True,
    include_delegation: bool = True,
    recovery_status: str = "ok",
) -> Path:
    db = tmp_path / "observer.sqlite3"
    store = EventStore(db)
    store.append("on_session_start", {
        "session_id": "root",
        "platform": "cli",
        "model": "fixture-model",
    })
    session = "root"
    if include_delegation:
        store.append("subagent_start", {
            "parent_session_id": "root",
            "parent_turn_id": "pt1",
            "child_session_id": "child",
            "child_subagent_id": "sub1",
            "child_role": "leaf",
        })
        session = "child"
    store.append("post_tool_call", {
        "session_id": session,
        "task_id": "task-1",
        "turn_id": "turn-fail",
        "tool_call_id": "tool-fail",
        "tool_name": "terminal",
        "status": "error",
        "error_type": "tool_error",
        "error_message": "sensitive failing-test output",
    })
    if include_recovery:
        store.append("post_tool_call", {
            "session_id": session,
            "task_id": "task-1",
            "turn_id": "turn-recovery",
            "tool_call_id": "tool-recovery",
            "tool_name": "terminal",
            "status": recovery_status,
            "result": "sensitive passing-test output",
        })
    if include_delegation:
        store.append("subagent_stop", {
            "parent_session_id": "root",
            "parent_turn_id": "pt1",
            "child_session_id": "child",
            "child_role": "leaf",
            "child_status": "completed",
        })
    target = tmp_path / "capture"
    create_bundle(db, target)
    return target


def test_e1_validation_accepts_current_hermes_ok_recovery_status(tmp_path: Path):
    result = validate(_capture(tmp_path, recovery_status="ok"))
    assert result["passed"] is True
    assert all(result["checks"].values())
    assert result["counts"]["same_agent_failure_recovery_pairs"] == 1


def test_e1_validation_keeps_backward_success_status_compatible(tmp_path: Path):
    result = validate(_capture(tmp_path, recovery_status="success"))
    assert result["passed"] is True
    assert result["counts"]["tool_successes"] == 1


def test_e1_validation_rejects_unknown_recovery_status(tmp_path: Path):
    result = validate(_capture(tmp_path, recovery_status="unknown"))
    assert result["passed"] is False
    assert result["checks"]["has_later_same_agent_tool_success"] is False


def test_e1_validation_rejects_missing_recovery(tmp_path: Path):
    result = validate(_capture(tmp_path, include_recovery=False))
    assert result["passed"] is False
    assert result["checks"]["has_tool_error"] is True
    assert result["checks"]["has_later_same_agent_tool_success"] is False


def test_e1_validation_rejects_missing_delegation(tmp_path: Path):
    result = validate(_capture(tmp_path, include_delegation=False))
    assert result["passed"] is False
    assert result["checks"]["has_delegation_start"] is False
    assert result["checks"]["has_interaction_state"] is False
