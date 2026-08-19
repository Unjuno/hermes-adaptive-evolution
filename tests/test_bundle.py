from __future__ import annotations

import json
from pathlib import Path

import pytest

from adaptive_evolution_observer.bundle import create_bundle, replay_bundle
from adaptive_evolution_observer.cli import status
from adaptive_evolution_observer.store import EventStore


def _fixture_db(tmp_path: Path) -> Path:
    db = tmp_path / "observer.sqlite3"
    store = EventStore(db)
    store.append("on_session_start", {"session_id": "root"})
    store.append("subagent_start", {
        "parent_session_id": "root",
        "parent_turn_id": "t1",
        "child_session_id": "child",
        "child_subagent_id": "sub1",
        "child_role": "leaf",
        "child_goal": "sensitive goal",
    })
    store.append("post_tool_call", {
        "session_id": "child",
        "turn_id": "ct1",
        "tool_call_id": "tc1",
        "tool_name": "python",
        "status": "success",
        "args": {"api_key": "secret-value"},
        "result": "sensitive output",
    })
    return db


def test_bundle_roundtrip_matches_direct_replay(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_CAPTURE_CONTENT", raising=False)
    db = _fixture_db(tmp_path)
    target = tmp_path / "bundle"

    created = create_bundle(db, target)
    replayed = replay_bundle(target)
    direct = status(db)

    assert created["manifest"]["schema"] == "adaptive-evolution.capture-bundle.v0.2"
    assert replayed["matches_manifest_state"] is True
    assert replayed["normalization_matches_trace"] is True
    assert replayed["state"] == direct["state"]
    assert created["manifest"]["privacy"]["raw_sqlite_included"] is False
    assert created["manifest"]["privacy"]["raw_event_stream_is_pre_sanitized"] is True
    assert created["manifest"]["source"] == {"database_name": "observer.sqlite3"}

    raw_trace = (target / "sanitized-raw-events.jsonl").read_text(encoding="utf-8")
    normalized_trace = (target / "normalized-events.jsonl").read_text(encoding="utf-8")
    for secret in ("secret-value", "sensitive output", "sensitive goal"):
        assert secret not in raw_trace
        assert secret not in normalized_trace
    assert str(tmp_path) not in (target / "manifest.json").read_text(encoding="utf-8")


def test_bundle_checksum_detects_normalized_trace_mutation(tmp_path: Path):
    db = _fixture_db(tmp_path)
    target = tmp_path / "bundle"
    create_bundle(db, target)
    trace_path = target / "normalized-events.jsonl"
    trace_path.write_text(trace_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="normalized trace checksum mismatch"):
        replay_bundle(target)


def test_bundle_checksum_detects_sanitized_raw_trace_mutation(tmp_path: Path):
    db = _fixture_db(tmp_path)
    target = tmp_path / "bundle"
    create_bundle(db, target)
    trace_path = target / "sanitized-raw-events.jsonl"
    trace_path.write_text(trace_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="sanitized raw trace checksum mismatch"):
        replay_bundle(target)


def test_bundle_manifest_is_machine_readable(tmp_path: Path):
    db = _fixture_db(tmp_path)
    target = tmp_path / "bundle"
    create_bundle(db, target)
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sanitized_raw_trace"]["file"] == "sanitized-raw-events.jsonl"
    assert manifest["normalized_trace"]["file"] == "normalized-events.jsonl"
    assert len(manifest["sanitized_raw_trace"]["sha256"]) == 64
    assert len(manifest["normalized_trace"]["sha256"]) == 64
    assert manifest["event_diagnostics"]["unique_count"] == 3
