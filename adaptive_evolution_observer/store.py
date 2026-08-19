from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = {
    "token", "api_key", "apikey", "authorization", "password", "secret",
    "cookie", "access_token", "refresh_token", "headers", "conversation_history",
    "request_messages", "user_message", "assistant_response", "response_text",
    "final_response", "child_goal",
}
CONTENT_KEYS = {
    "args", "result", "request", "response", "assistant_message", "error",
    "error_message", "reason", "summary", "child_summary", "tool_input",
    "tool_output",
}


def default_data_dir() -> Path:
    explicit = os.getenv("ADAPTIVE_EVOLUTION_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser()
    hermes_home = os.getenv("HERMES_HOME")
    if hermes_home:
        return Path(hermes_home).expanduser() / "adaptive-evolution"
    return Path.home() / ".hermes" / "adaptive-evolution"


def resolve_db_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).expanduser()
    explicit = os.getenv("ADAPTIVE_EVOLUTION_OBSERVER_DB")
    if explicit:
        return Path(explicit).expanduser()
    return default_data_dir() / "observer.sqlite3"


def _clip_string(value: str, limit: int = 512) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"…<{len(value)-limit} chars omitted>"


def sanitize(value: Any, *, key: str = "", depth: int = 0) -> Any:
    """Bound/redact telemetry before persistence.

    The recorder is intentionally metadata-first. Raw prompt/tool content is not
    retained by default even when the Hermes hook exposes it. Secret-bearing
    values are never fingerprinted: a short hash of a low-entropy password,
    token, or proprietary goal would still enable offline guessing/linkage.
    """
    if depth > 6:
        return "<max-depth>"
    lk = key.lower()
    if lk in SENSITIVE_KEYS or any(part in lk for part in ("password", "secret", "token")):
        if isinstance(value, str):
            return {"redacted": True, "length": len(value)}
        return "<redacted>"
    if lk in CONTENT_KEYS and os.getenv("ADAPTIVE_EVOLUTION_CAPTURE_CONTENT", "0") != "1":
        if isinstance(value, dict):
            allowed = {
                k: v for k, v in value.items()
                if str(k).lower() in {
                    "ok", "success", "status", "error", "error_type",
                    "error_message", "reason", "type", "exit_code",
                }
            }
            return sanitize(allowed, depth=depth + 1)
        if isinstance(value, str):
            return {"content_omitted": True, "length": len(value)}
        return "<content-omitted>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _clip_string(value)
    if isinstance(value, bytes):
        return {"bytes": len(value)}
    if isinstance(value, dict):
        out = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 80:
                out["<truncated>"] = len(value) - 80
                break
            out[str(k)] = sanitize(v, key=str(k), depth=depth + 1)
        return out
    if isinstance(value, (list, tuple, set)):
        items = list(value)
        return [sanitize(v, depth=depth + 1) for v in items[:80]] + (["<truncated>"] if len(items) > 80 else [])
    return _clip_string(repr(value), 256)


def event_key(hook: str, payload: dict[str, Any]) -> str:
    """Best-effort event identity using hook-specific correlation fields.

    A Hermes correlation ID is not always itself an event ID. API retries may
    share ``api_request_id`` while ``retry_count`` changes, and Skill lifecycle
    events may share session/action/skill while ``use_count`` advances. Those
    fields therefore participate in the key rather than being collapsed as
    duplicates.
    """
    common = (
        "session_id", "task_id", "turn_id", "tool_call_id", "api_request_id",
        "parent_turn_id", "parent_subagent_id", "child_session_id", "child_subagent_id",
        "run_id", "action", "skill_name",
    )
    hook_specific: dict[str, tuple[str, ...]] = {
        "api_request_error": ("retry_count", "max_retries"),
        "on_skill_lifecycle": ("use_count", "reused", "reuse_after_patch", "provenance"),
        "on_session_reset": ("old_session_id", "new_session_id"),
    }

    parts = [hook]
    for k in common + hook_specific.get(hook, ()):
        v = payload.get(k)
        if v not in (None, ""):
            parts.append(f"{k}={v}")
    if len(parts) == 1:
        for k in ("tool_name", "child_role", "profile_name", "board", "status", "reason"):
            v = payload.get(k)
            if v not in (None, ""):
                parts.append(f"{k}={v}")
    raw = "|".join(map(str, parts))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class EventStore:
    def __init__(self, path: str | Path | None = None):
        self.path = resolve_db_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._con: sqlite3.Connection | None = None
        self._pid: int | None = None
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        pid = os.getpid()
        if self._con is None or self._pid != pid:
            try:
                if self._con is not None:
                    self._con.close()
            except Exception:
                pass
            con = sqlite3.connect(self.path, timeout=10, check_same_thread=False, isolation_level=None)
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("PRAGMA busy_timeout=10000")
            self._con = con
            self._pid = pid
        return self._con

    def close(self) -> None:
        """Close the process-local connection; future operations reopen lazily."""
        with self._lock:
            con = self._con
            self._con = None
            self._pid = None
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass

    def _init_db(self) -> None:
        with self._lock:
            con = self._connect()
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS raw_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    received_at_ns INTEGER NOT NULL,
                    pid INTEGER NOT NULL,
                    hook TEXT NOT NULL,
                    event_key TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_raw_events_time ON raw_events(received_at_ns, id);
                CREATE INDEX IF NOT EXISTS idx_raw_events_key ON raw_events(event_key);
                """
            )

    def append(self, hook: str, payload: dict[str, Any]) -> int:
        safe = sanitize(payload)
        assert isinstance(safe, dict)
        key = event_key(hook, safe)
        encoded = json.dumps(safe, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self._lock:
            con = self._connect()
            cur = con.execute(
                "INSERT INTO raw_events(received_at_ns,pid,hook,event_key,payload_json) VALUES(?,?,?,?,?)",
                (time.time_ns(), os.getpid(), hook, key, encoded),
            )
            return int(cur.lastrowid)

    def load(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT id,received_at_ns,pid,hook,event_key,payload_json FROM raw_events ORDER BY received_at_ns,id"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query = "SELECT * FROM (SELECT id,received_at_ns,pid,hook,event_key,payload_json FROM raw_events ORDER BY received_at_ns DESC,id DESC LIMIT ?) ORDER BY received_at_ns,id"
            params = (int(limit),)
        with self._lock:
            rows = self._connect().execute(query, params).fetchall()
        return [
            {
                "id": r[0], "received_at_ns": r[1], "pid": r[2], "hook": r[3],
                "event_key": r[4], "payload": json.loads(r[5]),
            }
            for r in rows
        ]

    def count(self) -> int:
        with self._lock:
            return int(self._connect().execute("SELECT COUNT(*) FROM raw_events").fetchone()[0])
