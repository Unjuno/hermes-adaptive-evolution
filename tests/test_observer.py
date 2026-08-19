from __future__ import annotations

import json
from pathlib import Path

import adaptive_evolution_observer.plugin as plugin_mod
from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import normalize
from adaptive_evolution_observer.plugin import HOOKS, handle_status, register
from adaptive_evolution_observer.store import EventStore, resolve_db_path, sanitize


class FakeContext:
    def __init__(self):
        self.hooks = {}
        self.tools = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback

    def register_tool(self, *, name, handler, **kwargs):
        self.tools[name] = {"handler": handler, **kwargs}


def test_registers_observer_surface_only():
    ctx = FakeContext()
    register(ctx)
    assert set(ctx.hooks) == set(HOOKS)
    assert "pre_tool_call" not in ctx.hooks
    assert "adaptive_evolution_observer_status" in ctx.tools
    assert "adaptive_evolution_observer_export" in ctx.tools


def test_sanitize_is_metadata_first(monkeypatch):
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_CAPTURE_CONTENT", raising=False)
    payload = sanitize({
        "api_key": "super-secret",
        "args": {"path": "/tmp/x", "token": "nested-secret"},
        "error_message": "sensitive failure text",
        "status": "error",
    })
    assert payload["api_key"]["redacted"] is True
    assert payload["args"] == {}
    assert payload["error_message"]["content_omitted"] is True
    assert payload["status"] == "error"


def _rows():
    return [
        {
            "id": 1,
            "received_at_ns": 1,
            "hook": "on_session_start",
            "event_key": "s1",
            "payload": {"session_id": "root", "platform": "cli"},
        },
        {
            "id": 2,
            "received_at_ns": 2,
            "hook": "subagent_start",
            "event_key": "a1",
            "payload": {
                "parent_session_id": "root",
                "parent_turn_id": "t1",
                "child_session_id": "child",
                "child_subagent_id": "sub1",
                "child_role": "leaf",
            },
        },
        {
            "id": 3,
            "received_at_ns": 3,
            "hook": "post_tool_call",
            "event_key": "tool1",
            "payload": {
                "session_id": "child",
                "turn_id": "ct1",
                "tool_call_id": "tc1",
                "tool_name": "web_search",
                "status": "success",
            },
        },
    ]


def test_normalize_is_order_independent_for_strong_ids():
    rows = _rows()
    a, da = normalize(rows)
    b, db = normalize(list(reversed(rows)) + [dict(rows[2])])
    project = lambda xs: sorted(
        (e.event_key, e.agent_id, e.parent_agent_id, e.kind) for e in xs
    )
    assert project(a) == project(b)
    assert db["duplicates_removed"] == 1
    assert da["uncertain_session_events"] == 0


def test_missing_subagent_start_does_not_invent_identity():
    rows = [r for r in _rows() if r["hook"] != "subagent_start"]
    events, diag = normalize(rows)
    tool = next(e for e in events if e.kind == "tool_result")
    assert tool.agent_id == "session:child"
    assert diag["uncertain_session_events"] >= 1


def test_subagent_session_start_is_not_root_evidence_without_start_edge():
    rows = [
        {
            "id": 1,
            "received_at_ns": 1,
            "hook": "on_session_start",
            "event_key": "child-session-start",
            "payload": {"session_id": "child", "platform": "subagent"},
        },
        {
            "id": 2,
            "received_at_ns": 2,
            "hook": "post_tool_call",
            "event_key": "child-tool",
            "payload": {
                "session_id": "child",
                "turn_id": "ct1",
                "tool_call_id": "tc1",
                "tool_name": "python",
                "status": "success",
            },
        },
    ]
    events, diag = normalize(rows)
    start = next(e for e in events if e.kind == "on_session_start")
    tool = next(e for e in events if e.kind == "tool_result")
    assert start.agent_id == "session:child"
    assert tool.agent_id == "session:child"
    assert diag["known_root_sessions"] == 0
    assert diag["uncertain_session_events"] >= 2


def test_explicit_subagent_start_overrides_session_start_hint():
    rows = _rows() + [
        {
            "id": 4,
            "received_at_ns": 4,
            "hook": "on_session_start",
            "event_key": "child-start-extra",
            "payload": {"session_id": "child"},
        }
    ]
    events, diag = normalize(rows)
    child_events = [e for e in events if e.session_id == "child"]
    assert child_events
    assert all(e.agent_id == "subagent:sub1" for e in child_events)
    assert diag["known_root_sessions"] == 1


def test_estimator_produces_diagnostic_state():
    events, _ = normalize(_rows())
    state = estimate(events)
    assert state["authority"] == "diagnostic_only"
    assert state["agents"] >= 2
    assert state["interaction_events"] == 1
    assert state["traffic_weighted_role_mixing"] is not None


def test_store_roundtrip(tmp_path: Path):
    store = EventStore(tmp_path / "observer.sqlite3")
    store.append("on_session_start", {"session_id": "root"})
    rows = store.load()
    assert len(rows) == 1
    assert rows[0]["payload"]["session_id"] == "root"


def test_default_db_path_respects_hermes_home(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_OBSERVER_DB", raising=False)
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_DATA_DIR", raising=False)
    home = tmp_path / "profile-a"
    monkeypatch.setenv("HERMES_HOME", str(home))
    assert resolve_db_path() == home / "adaptive-evolution" / "observer.sqlite3"


def test_plugin_store_rebinds_when_profile_changes(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_OBSERVER_DB", raising=False)
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_DATA_DIR", raising=False)
    plugin_mod._STORE = None
    plugin_mod._STORE_PATH = None
    try:
        home_a = tmp_path / "profile-a"
        home_b = tmp_path / "profile-b"
        monkeypatch.setenv("HERMES_HOME", str(home_a))
        first = plugin_mod._store()
        monkeypatch.setenv("HERMES_HOME", str(home_b))
        second = plugin_mod._store()
        assert first.path != second.path
        assert first.path == home_a / "adaptive-evolution" / "observer.sqlite3"
        assert second.path == home_b / "adaptive-evolution" / "observer.sqlite3"
    finally:
        plugin_mod._STORE = None
        plugin_mod._STORE_PATH = None


def test_status_limit_validation(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("ADAPTIVE_EVOLUTION_OBSERVER_DB", str(tmp_path / "status.sqlite3"))
    out = json.loads(handle_status({"limit": "bad"}))
    assert out["success"] is False
