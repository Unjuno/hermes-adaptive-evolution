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

BUNDLE_SCHEMA = "adaptive-evolution.capture-bundle.v0.2"
RAW_TRACE_NAME = "sanitized-raw-events.jsonl"
NORMALIZED_TRACE_NAME = "normalized-events.jsonl"
MANIFEST_NAME = "manifest.json"


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _event_dict(event: CanonicalEvent) -> dict[str, Any]:
    return {
        "seq": event.seq,
        "observed_at_ns": event.observed_at_ns,
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


def _raw_row_dict(row: dict[str, Any]) -> dict[str, Any]:
    # EventStore payloads are sanitized before persistence. Exclude DB-local
    # row ids and pids from the portable artifact; replay only needs timestamp,
    # hook, correlation key, and sanitized payload.
    return {
        "received_at_ns": int(row["received_at_ns"]),
        "hook": str(row["hook"]),
        "event_key": str(row["event_key"]),
        "payload": dict(row.get("payload") or {}),
    }


def _encode_jsonl(rows: list[dict[str, Any]]) -> bytes:
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    text = "\n".join(lines)
    if lines:
        text += "\n"
    return text.encode("utf-8")


def _encode_normalized(events: list[CanonicalEvent]) -> bytes:
    return _encode_jsonl([_event_dict(event) for event in events])


def _read_jsonl(data: bytes, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            raise ValueError(f"invalid {label} JSON at line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"invalid {label} row at line {line_number}: expected object")
        rows.append(row)
    return rows


def create_bundle(db: str | Path | None, directory: str | Path) -> dict[str, Any]:
    store = EventStore(db)
    raw_rows = store.load()
    events, diagnostics = normalize(raw_rows)
    target = Path(directory).expanduser()
    target.mkdir(parents=True, exist_ok=True)

    raw_bytes = _encode_jsonl([_raw_row_dict(row) for row in raw_rows])
    raw_path = target / RAW_TRACE_NAME
    raw_path.write_bytes(raw_bytes)
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    normalized_bytes = _encode_normalized(events)
    normalized_path = target / NORMALIZED_TRACE_NAME
    normalized_path.write_bytes(normalized_bytes)
    normalized_sha256 = hashlib.sha256(normalized_bytes).hexdigest()

    state = estimate(events)
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sanitized_raw_trace": {
            "file": RAW_TRACE_NAME,
            "sha256": raw_sha256,
            "events": len(raw_rows),
        },
        "normalized_trace": {
            "file": NORMALIZED_TRACE_NAME,
            "sha256": normalized_sha256,
            "events": len(events),
        },
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
            "raw_event_stream_is_pre_sanitized": True,
        },
        "source": {
            "database_name": store.path.name,
        },
    }
    manifest_path = target / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"directory": str(target), "manifest": manifest}


def replay_bundle(directory: str | Path) -> dict[str, Any]:
    root = Path(directory).expanduser()
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    if manifest.get("schema") != BUNDLE_SCHEMA:
        raise ValueError(f"unsupported bundle schema: {manifest.get('schema')!r}")

    raw_meta = dict(manifest.get("sanitized_raw_trace") or {})
    normalized_meta = dict(manifest.get("normalized_trace") or {})
    raw_path = root / str(raw_meta.get("file") or RAW_TRACE_NAME)
    normalized_path = root / str(normalized_meta.get("file") or NORMALIZED_TRACE_NAME)

    raw_bytes = raw_path.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != raw_meta.get("sha256"):
        raise ValueError(
            f"sanitized raw trace checksum mismatch: expected {raw_meta.get('sha256')}, got {raw_sha}"
        )

    normalized_bytes = normalized_path.read_bytes()
    normalized_sha = hashlib.sha256(normalized_bytes).hexdigest()
    if normalized_sha != normalized_meta.get("sha256"):
        raise ValueError(
            f"normalized trace checksum mismatch: expected {normalized_meta.get('sha256')}, got {normalized_sha}"
        )

    raw_rows = _read_jsonl(raw_bytes, "sanitized raw trace")
    replayed_events, replayed_diag = normalize(raw_rows)
    replayed_normalized = _encode_normalized(replayed_events)
    normalization_matches_trace = replayed_normalized == normalized_bytes
    state = estimate(replayed_events)

    return {
        "schema": manifest["schema"],
        "directory": str(root),
        "raw_events": len(raw_rows),
        "normalized_events": len(replayed_events),
        "raw_trace_sha256": raw_sha,
        "normalized_trace_sha256": normalized_sha,
        "normalization_matches_trace": normalization_matches_trace,
        "event_diagnostics": replayed_diag,
        "state": state,
        "matches_manifest_state": state == manifest.get("organization_state"),
    }
