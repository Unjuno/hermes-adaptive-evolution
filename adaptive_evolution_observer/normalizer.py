from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanonicalEvent:
    seq: int
    hook: str
    event_key: str
    session_id: str | None
    task_id: str | None
    turn_id: str | None
    agent_id: str | None
    parent_agent_id: str | None
    kind: str
    data: dict[str, Any]


def _root_agent(session_id: str | None) -> str | None:
    return f"root:{session_id}" if session_id else None


def _child_agent(subagent_id: str | None, child_session_id: str | None) -> str | None:
    if subagent_id:
        return f"subagent:{subagent_id}"
    if child_session_id:
        return f"child-session:{child_session_id}"
    return None


def normalize(raw_events: list[dict[str, Any]]) -> tuple[list[CanonicalEvent], dict[str, Any]]:
    """Normalize/deduplicate raw hook records.

    Two-pass identity resolution makes mild reordering harmless: a child tool
    event can arrive before its corresponding subagent_start record and still be
    attributed correctly during replay.
    """
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates = 0

    def dedup_safe(row: dict[str, Any]) -> bool:
        hook = row["hook"]
        p = row["payload"]
        if hook == "post_tool_call":
            return bool(p.get("tool_call_id"))
        if hook == "api_request_error":
            return bool(p.get("api_request_id"))
        if hook in {"subagent_start", "subagent_stop"}:
            return bool(p.get("child_subagent_id") or p.get("child_session_id"))
        if hook == "on_session_start":
            return bool(p.get("session_id"))
        if hook == "on_session_end":
            return bool(p.get("session_id") and p.get("turn_id"))
        if hook in {"on_session_finalize", "on_session_reset"}:
            return bool(p.get("session_id") and (p.get("reason") or p.get("old_session_id") or p.get("new_session_id")))
        if hook == "on_skill_lifecycle":
            return bool(p.get("session_id") and p.get("skill_name") and p.get("action") and p.get("use_count") is not None)
        return False

    for row in raw_events:
        k = row["event_key"]
        if dedup_safe(row) and k in seen:
            duplicates += 1
            continue
        if dedup_safe(row):
            seen.add(k)
        unique.append(row)

    session_to_agent: dict[str, str] = {}
    session_to_role: dict[str, str] = {}
    root_sessions: set[str] = set()
    for row in unique:
        p = row["payload"]
        if row["hook"] == "on_session_start" and p.get("session_id"):
            root_sessions.add(str(p["session_id"]))
        if row["hook"] != "subagent_start":
            continue
        child_session = p.get("child_session_id")
        child_agent = _child_agent(p.get("child_subagent_id"), child_session)
        if child_session and child_agent:
            session_to_agent[str(child_session)] = child_agent
            if p.get("child_role"):
                session_to_role[str(child_session)] = str(p["child_role"])
        parent_session = p.get("parent_session_id")
        if parent_session and not p.get("parent_subagent_id"):
            root_sessions.add(str(parent_session))

    uncertain_session_events = 0

    def resolve_session(sid: Any) -> tuple[str | None, bool]:
        if not sid:
            return None, False
        ss = str(sid)
        if ss in session_to_agent:
            return session_to_agent[ss], False
        if ss in root_sessions:
            return _root_agent(ss), False
        return f"session:{ss}", True

    out: list[CanonicalEvent] = []
    unattributed = 0
    for seq, row in enumerate(unique, 1):
        hook = row["hook"]
        p = row["payload"]
        session_id = p.get("session_id") or p.get("child_session_id")
        task_id = p.get("task_id")
        turn_id = p.get("turn_id") or p.get("parent_turn_id")
        agent_id: str | None = None
        parent_id: str | None = None
        kind = "observer"
        data: dict[str, Any] = {}

        if hook == "subagent_start":
            agent_id = _child_agent(p.get("child_subagent_id"), p.get("child_session_id"))
            parent_id = _child_agent(p.get("parent_subagent_id"), None) or _root_agent(p.get("parent_session_id"))
            kind = "interaction_start"
            data = {"role": p.get("child_role"), "goal": p.get("child_goal")}
        elif hook == "subagent_stop":
            child_session = p.get("child_session_id")
            agent_id, uncertain_child = resolve_session(child_session)
            parent_id, uncertain_parent = resolve_session(p.get("parent_session_id"))
            uncertain_session_events += int(uncertain_child) + int(uncertain_parent)
            kind = "interaction_stop"
            data = {
                "role": p.get("child_role"), "status": p.get("child_status"),
                "duration_ms": p.get("duration_ms"), "tool_call_history": p.get("tool_call_history"),
            }
        elif hook in {"pre_tool_call", "post_tool_call", "pre_api_request", "post_api_request", "api_request_error", "on_skill_lifecycle"}:
            sid = p.get("session_id")
            agent_id, uncertain = resolve_session(sid)
            uncertain_session_events += int(uncertain)
            if hook == "post_tool_call":
                kind = "tool_result"
                data = {k: p.get(k) for k in ("tool_name", "status", "error_type", "error_message", "duration_ms", "tool_call_id")}
            elif hook == "pre_tool_call":
                kind = "tool_start"
                data = {k: p.get(k) for k in ("tool_name", "tool_call_id")}
            elif hook == "api_request_error":
                kind = "api_error"
                data = {k: p.get(k) for k in ("provider", "model", "status_code", "retry_count", "retryable", "reason")}
            elif hook in {"pre_api_request", "post_api_request"}:
                kind = "api_request" if hook == "pre_api_request" else "api_response"
                data = {k: p.get(k) for k in ("provider", "model", "api_call_count", "retry_count", "api_duration", "finish_reason")}
            else:
                kind = "skill"
                data = {k: p.get(k) for k in ("action", "skill_name", "provenance", "use_count", "reused", "reuse_after_patch")}
        elif hook.startswith("kanban_task_"):
            kind = hook
            agent_id = f"worker:{p.get('assignee')}" if p.get("assignee") else None
            data = {k: p.get(k) for k in ("profile_name", "board", "assignee", "run_id", "reason")}
        elif hook.startswith("on_session_"):
            agent_id, uncertain = resolve_session(p.get("session_id"))
            uncertain_session_events += int(uncertain)
            kind = hook
            data = {k: p.get(k) for k in ("completed", "failed", "interrupted", "turn_exit_reason", "model", "platform", "reason")}
        else:
            sid = p.get("session_id")
            agent_id, uncertain = resolve_session(sid)
            uncertain_session_events += int(uncertain)

        if kind in {"tool_result", "tool_start", "api_error", "api_request", "api_response", "skill"} and not agent_id:
            unattributed += 1

        out.append(CanonicalEvent(
            seq=seq,
            hook=hook,
            event_key=row["event_key"],
            session_id=str(session_id) if session_id else None,
            task_id=str(task_id) if task_id else None,
            turn_id=str(turn_id) if turn_id else None,
            agent_id=agent_id,
            parent_agent_id=parent_id,
            kind=kind,
            data=data,
        ))

    diagnostics = {
        "raw_count": len(raw_events),
        "unique_count": len(unique),
        "duplicates_removed": duplicates,
        "known_child_sessions": len(session_to_agent),
        "unattributed_observer_events": unattributed,
        "uncertain_session_events": uncertain_session_events,
        "known_root_sessions": len(root_sessions),
    }
    return out, diagnostics
