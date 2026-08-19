from __future__ import annotations

from pathlib import Path

from adaptive_evolution_observer.bundle import create_bundle
from adaptive_evolution_observer.store import EventStore
from experiments.report_hook_coverage import report


def _capture(tmp_path: Path) -> Path:
    db = tmp_path / "observer.sqlite3"
    store = EventStore(db)
    store.append("on_session_start", {
        "session_id": "root",
        "model": "fixture-model",
        "platform": "cli",
        "unexpected_additive": "present",
    })
    store.append("subagent_start", {
        "parent_session_id": "root",
        "parent_turn_id": "pt1",
        "child_session_id": "child",
        "child_subagent_id": "sub1",
        "child_role": "leaf",
    })
    store.append("subagent_stop", {
        "parent_session_id": "root",
        "parent_turn_id": "pt1",
        "child_session_id": "child",
        "child_role": "leaf",
        "child_status": "completed",
        "duration_ms": 10,
    })
    store.append("post_tool_call", {
        "session_id": "child",
        "task_id": "task-1",
        "turn_id": "turn-1",
        "tool_call_id": "tool-1",
        "tool_name": "python",
        "duration_ms": 1,
        "status": "success",
    })
    bundle = tmp_path / "capture"
    create_bundle(db, bundle)
    return bundle


def test_hook_coverage_reports_presence_without_values(tmp_path: Path):
    result = report(_capture(tmp_path))
    assert result["events"] == 4
    assert result["identity"]["stop_sessions_without_start"] == 0
    tool = result["hooks"]["post_tool_call"]
    assert tool["fields"]["tool_call_id"]["fraction"] == 1.0
    assert tool["fields"]["api_request_id"]["fraction"] == 0.0
    assert "api_request_id" in tool["missing_expected_fields_entirely"]
    assert "tool-1" not in str(result)


def test_hook_coverage_tracks_additive_fields_separately(tmp_path: Path):
    result = report(_capture(tmp_path))
    session = result["hooks"]["on_session_start"]
    assert "unexpected_additive" in session["additive_fields_not_in_checked_contract"]
    assert session["fields"]["unexpected_additive"]["expected_by_current_contract"] is False
