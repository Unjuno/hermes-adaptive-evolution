from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .estimator import estimate
from .normalizer import normalize
from .store import EventStore

# Observer hooks only. Directive hooks are intentionally excluded from v0.2 so
# this slice cannot change execution behavior while M1/M2 contracts are tested.
HOOKS = (
    "on_session_start",
    "on_session_end",
    "on_session_finalize",
    "on_session_reset",
    "post_tool_call",
    "api_request_error",
    "on_skill_lifecycle",
    "subagent_start",
    "subagent_stop",
    "kanban_task_claimed",
    "kanban_task_completed",
    "kanban_task_blocked",
)


_STORE: EventStore | None = None
_STORE_PATH: str | None = None


def _store() -> EventStore:
    global _STORE, _STORE_PATH
    path = os.getenv("ADAPTIVE_EVOLUTION_OBSERVER_DB")
    if _STORE is None or _STORE_PATH != path:
        _STORE = EventStore(path)
        _STORE_PATH = path
    return _STORE


def _record(hook: str, **kwargs: Any) -> None:
    try:
        _store().append(hook, kwargs)
    except Exception:
        # Hermes itself already isolates hook failures; keep this plugin
        # fail-open as an observer even when its storage is unavailable.
        return


def _status_payload(limit: int | None = None) -> dict[str, Any]:
    store = _store()
    raw = store.load(limit=limit)
    canonical, diag = normalize(raw)
    state = estimate(canonical)
    return {"events": diag, "state": state, "database": str(store.path)}


def handle_status(params: dict, **kwargs: Any) -> str:
    del kwargs
    limit = params.get("limit")
    if limit is not None:
        try:
            limit = max(1, min(int(limit), 50000))
        except (TypeError, ValueError):
            return json.dumps({"success": False, "error": "limit must be an integer"})
    return json.dumps({"success": True, **_status_payload(limit)}, ensure_ascii=False)


def handle_export(params: dict, **kwargs: Any) -> str:
    del kwargs
    path = params.get("path")
    if not path:
        data_dir = Path(os.getenv("ADAPTIVE_EVOLUTION_DATA_DIR", Path.home() / ".hermes" / "adaptive-evolution"))
        path = data_dir / "normalized-events.jsonl"
    else:
        path = Path(path).expanduser()
    store = _store()
    canonical, diag = normalize(store.load())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in canonical:
            f.write(json.dumps({
                "seq": e.seq, "hook": e.hook, "event_key": e.event_key,
                "session_id": e.session_id, "task_id": e.task_id, "turn_id": e.turn_id,
                "agent_id": e.agent_id, "parent_agent_id": e.parent_agent_id,
                "kind": e.kind, "data": e.data,
            }, ensure_ascii=False, sort_keys=True) + "\n")
    return json.dumps({"success": True, "path": str(path), "events": diag}, ensure_ascii=False)


def register(ctx) -> None:
    for hook in HOOKS:
        def callback(_hook=hook, **kwargs):
            _record(_hook, **kwargs)
        ctx.register_hook(hook, callback)

    ctx.register_tool(
        name="adaptive_evolution_observer_status",
        toolset="adaptive_evolution",
        schema={
            "name": "adaptive_evolution_observer_status",
            "description": "Return experimental organization-state telemetry inferred from Hermes observer hooks.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50000}},
            },
        },
        handler=handle_status,
        description="Inspect experimental adaptive-evolution organization state.",
    )
    ctx.register_tool(
        name="adaptive_evolution_observer_export",
        toolset="adaptive_evolution",
        schema={
            "name": "adaptive_evolution_observer_export",
            "description": "Export deduplicated normalized observer events as JSONL.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        },
        handler=handle_export,
        description="Export normalized adaptive-evolution observer events.",
    )
