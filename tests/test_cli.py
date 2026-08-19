from __future__ import annotations

import json
from pathlib import Path

from adaptive_evolution_observer.cli import export, main, status
from adaptive_evolution_observer.store import EventStore


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "observer.sqlite3"
    store = EventStore(path)
    store.append("on_session_start", {"session_id": "root", "platform": "cli"})
    store.append("post_tool_call", {
        "session_id": "root",
        "turn_id": "t1",
        "tool_call_id": "tc1",
        "tool_name": "python",
        "status": "success",
    })
    return path


def test_status_reads_observer_db(tmp_path: Path):
    result = status(_db(tmp_path))
    assert result["events"]["unique_count"] == 2
    assert result["window"]["identity_context_preserved"] is True
    assert result["state"]["tool_outcomes"] == 1


def test_status_limit_preserves_child_identity_from_older_context(tmp_path: Path):
    path = tmp_path / "observer.sqlite3"
    store = EventStore(path)
    store.append("on_session_start", {"session_id": "root", "platform": "cli"})
    store.append("subagent_start", {
        "parent_session_id": "root",
        "parent_turn_id": "pt1",
        "child_session_id": "child",
        "child_subagent_id": "sub1",
        "child_role": "leaf",
    })
    for i in range(5):
        store.append("post_tool_call", {
            "session_id": "root",
            "turn_id": f"pt-{i}",
            "tool_call_id": f"root-{i}",
            "tool_name": "terminal",
            "status": "success",
        })
    store.append("post_tool_call", {
        "session_id": "child",
        "turn_id": "child-recent",
        "tool_call_id": "child-recent-tool",
        "tool_name": "web_search",
        "status": "success",
    })

    result = status(path, limit=1)
    assert result["window"] == {
        "requested_limit": 1,
        "context_events": 8,
        "selected_events": 1,
        "identity_context_preserved": True,
    }
    assert set(result["state"]["role_posteriors"]) == {"subagent:sub1"}
    assert result["events"]["uncertain_session_events"] == 0


def test_export_writes_normalized_jsonl(tmp_path: Path):
    db = _db(tmp_path)
    target = tmp_path / "trace.jsonl"
    result = export(db, target)
    assert result["path"] == str(target)
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert len(rows) == 2
    assert {row["kind"] for row in rows} == {"on_session_start", "tool_result"}
    assert all("observed_at_ns" in row for row in rows)


def test_main_prints_json(tmp_path: Path, capsys):
    db = _db(tmp_path)
    assert main(["--db", str(db), "status"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["database"] == str(db)
