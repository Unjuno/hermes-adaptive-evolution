from __future__ import annotations

import json
from pathlib import Path

from adaptive_evolution_observer.cli import export, main, status
from adaptive_evolution_observer.store import EventStore


def _db(tmp_path: Path) -> Path:
    path = tmp_path / "observer.sqlite3"
    store = EventStore(path)
    store.append("on_session_start", {"session_id": "root"})
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
    assert result["state"]["tool_outcomes"] == 1


def test_export_writes_normalized_jsonl(tmp_path: Path):
    db = _db(tmp_path)
    target = tmp_path / "trace.jsonl"
    result = export(db, target)
    assert result["path"] == str(target)
    rows = [json.loads(line) for line in target.read_text().splitlines()]
    assert len(rows) == 2
    assert {row["kind"] for row in rows} == {"on_session_start", "tool_result"}


def test_main_prints_json(tmp_path: Path, capsys):
    db = _db(tmp_path)
    assert main(["--db", str(db), "status"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["database"] == str(db)
