from __future__ import annotations

from typing import Any

from .store import EventStore, resolve_db_path

# M1/M2 is deliberately a pure observer. Registering model-facing tools would
# change the agent's tool schema and make the measurement system part of the
# behavior being measured. Analysis/export lives in the external CLI instead.
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
    path = resolve_db_path()
    key = str(path)
    if _STORE is None or _STORE_PATH != key:
        _STORE = EventStore(path)
        _STORE_PATH = key
    return _STORE


def _record(hook: str, **kwargs: Any) -> None:
    try:
        _store().append(hook, kwargs)
    except Exception:
        # Hermes itself isolates hook failures; remain fail-open even when the
        # observer's local storage is unavailable.
        return


def register(ctx) -> None:
    for hook in HOOKS:
        def callback(_hook=hook, **kwargs):
            _record(_hook, **kwargs)
        ctx.register_hook(hook, callback)
