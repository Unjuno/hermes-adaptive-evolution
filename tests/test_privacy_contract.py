from __future__ import annotations

import json
from pathlib import Path

from adaptive_evolution_observer.bundle import create_bundle
from adaptive_evolution_observer.store import EventStore, sanitize


def test_sensitive_strings_preserve_no_hash_or_value():
    secret = "correct horse battery staple"
    safe = sanitize({
        "password": secret,
        "api_key": "sk-fixture-secret",
        "child_goal": "short proprietary goal",
    })
    encoded = json.dumps(safe, sort_keys=True)
    for value in (secret, "sk-fixture-secret", "short proprietary goal"):
        assert value not in encoded
    assert "sha256" not in encoded.lower()
    assert safe["password"] == {"redacted": True, "length": len(secret)}


def test_capture_bundle_contains_no_secret_fingerprint(tmp_path: Path):
    db = tmp_path / "observer.sqlite3"
    store = EventStore(db)
    store.append("on_session_start", {"session_id": "root", "platform": "cli"})
    store.append("subagent_start", {
        "parent_session_id": "root",
        "parent_turn_id": "t1",
        "child_session_id": "child",
        "child_subagent_id": "sub1",
        "child_role": "leaf",
        "child_goal": "private-short-goal",
    })
    target = tmp_path / "capture"
    create_bundle(db, target)
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            target / "manifest.json",
            target / "sanitized-raw-events.jsonl",
            target / "normalized-events.jsonl",
        )
    )
    assert "private-short-goal" not in text
    assert "sha256_16" not in text
