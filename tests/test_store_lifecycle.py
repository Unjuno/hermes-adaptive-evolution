from __future__ import annotations

from pathlib import Path

import adaptive_evolution_observer.plugin as plugin_mod
from adaptive_evolution_observer.store import EventStore


def test_store_close_reopens_lazily(tmp_path: Path):
    store = EventStore(tmp_path / "observer.sqlite3")
    store.append("on_session_start", {"session_id": "a"})
    assert store._con is not None
    store.close()
    assert store._con is None
    assert store._pid is None
    store.append("on_session_end", {"session_id": "a", "turn_id": "t1"})
    assert store.count() == 2


def test_profile_rebind_closes_previous_store(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_OBSERVER_DB", raising=False)
    monkeypatch.delenv("ADAPTIVE_EVOLUTION_DATA_DIR", raising=False)
    plugin_mod._STORE = None
    plugin_mod._STORE_PATH = None
    try:
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "a"))
        first = plugin_mod._store()
        first.append("on_session_start", {"session_id": "a"})
        assert first._con is not None

        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "b"))
        second = plugin_mod._store()
        assert second is not first
        assert first._con is None
        assert second.path == tmp_path / "b" / "adaptive-evolution" / "observer.sqlite3"
    finally:
        if plugin_mod._STORE is not None:
            plugin_mod._STORE.close()
        plugin_mod._STORE = None
        plugin_mod._STORE_PATH = None
