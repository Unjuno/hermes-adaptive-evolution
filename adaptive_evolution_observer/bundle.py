from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .estimator import estimate
from .normalizer import CanonicalEvent, normalize
from .store import EventStore

BUNDLE_SCHEMA = "adaptive-evolution.capture-bundle.v0.1"
TRACE_NAME = "normalized-events.jsonl"
MANIFEST_NAME = "manifest.json"


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _event_dict(event: CanonicalEvent) -> dict[str, Any]:
    return {
        "seq": event.seq,
        "hook": event.hook,
        "event_key": event.event_key,
        "session_id": event.session_id,
        "task_id": event.task_id,
        "turn_id": event.turn_id,
        "agent_id": event.agent_id,
        "parent_agent_id": event.parent_agent_id,
        "kind": event.kind,
        "data": event.data,
    }


def _encode_trace(events: list[CanonicalEvent]) -> bytes:
    lines = [
        json.dumps(_event_dict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for event in events
    ]
    text = "\n".join(lines)
    if lines:
        text += "\n"
    return text.encode("utf-8")


def create_bundle(db: str | Path | None, directory: str | Path) -> dict[str, Any]:
    store = EventStore(db)
    events, diagnostics = normalize(store.load())
    target = Path(directory).expanduser()
    target.mkdir(parents=True, exist_ok=True)

    trace_bytes = _encode_trace(events)
    trace_path = target / TRACE_NAME
    trace_path.write_bytes(trace_bytes)
    trace_sha256 = hashlib.sha256(trace_bytes).hexdigest()

    state = estimate(events)
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "trace_file": TRACE_NAME,
        "trace_sha256": trace_sha256,
        "event_diagnostics": diagnostics,
        "organization_state": state,
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "hermes_agent_version": _distribution_version("hermes-agent"),
            "plugin_version": _distribution_version("hermes-adaptive-evolution"),
        },
        "privacy": {
            "capture_content": os.getenv("ADAPTIVE_EVOLUTION_CAPTURE_CONTENT", "0") == "1",
            "raw_sqlite_included": False,
        },
        "source": {
            # Avoid persisting an absolute operator path in a portable bundle.
            "database_name": store.path.name,
        },
    }
    manifest_path = target / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"directory": str(target), "manifest": manifest}


def _load_event(row: dict[str, Any]) -> CanonicalEvent:
    return CanonicalEvent(
        seq=int(row["seq"]),
        hook=str(row["hook"]),
        event_key=str(row["event_key"]),
        session_id=row.get("session_id"),
        task_id=row.get("task_id"),
        turn_id=row.get("turn_id"),
        agent_id=row.get("agent_id"),
        parent_agent_id=row.get("parent_agent_id"),
        kind=str(row["kind"]),
        data=dict(row.get("data") or {}),
    )


def replay_bundle(directory: str | Path) -> dict[str, Any]:
    root = Path(directory).expanduser()
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise ValueError(f"unsupported bundle schema: {manifest.get('schema')!r}")
    trace_path = root / str(manifest.get("trace_file") or TRACE_NAME)
    trace_bytes = trace_path.read_bytes()
    actual_sha = hashlib.sha256(trace_bytes).hexdigest()
    expected_sha = manifest.get("trace_sha256")
    if actual_sha != expected_sha:
        raise ValueError(
            f"trace checksum mismatch: expected {expected_sha}, got {actual_sha}"
        )

    events = []
    for line_number, line in enumerate(trace_bytes.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            events.append(_load_event(row))
        except Exception as exc:
            raise ValueError(f"invalid normalized event at line {line_number}: {exc}") from exc

    state = estimate(events)
    return {
        "schema": manifest["schema"],
        "directory": str(root),
        "events": len(events),
        "trace_sha256": actual_sha,
        "state": state,
        "matches_manifest_state": state == manifest.get("organization_state"),
    }
