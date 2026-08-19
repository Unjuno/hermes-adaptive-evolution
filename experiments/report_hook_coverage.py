from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

RAW_NAME = "sanitized-raw-events.jsonl"

EXPECTED_FIELDS: dict[str, tuple[str, ...]] = {
    "on_session_start": ("session_id", "model", "platform"),
    "on_session_end": (
        "session_id", "task_id", "turn_id", "completed", "failed",
        "interrupted", "turn_exit_reason", "model", "platform",
    ),
    "on_session_finalize": ("session_id", "platform"),
    "on_session_reset": ("session_id", "platform"),
    "post_tool_call": (
        "tool_name", "task_id", "session_id", "tool_call_id", "turn_id",
        "api_request_id", "duration_ms", "status", "error_type", "error_message",
    ),
    "api_request_error": (
        "task_id", "turn_id", "api_request_id", "session_id", "platform",
        "model", "provider", "status_code", "retry_count", "max_retries",
        "retryable", "reason", "error",
    ),
    "on_skill_lifecycle": (
        "action", "skill_name", "provenance", "task_id", "session_id",
        "use_count", "reused", "reuse_after_patch",
    ),
    "subagent_start": (
        "parent_session_id", "parent_turn_id", "parent_subagent_id",
        "child_session_id", "child_subagent_id", "child_role", "child_goal",
    ),
    "subagent_stop": (
        "parent_session_id", "parent_turn_id", "child_session_id", "child_role",
        "child_summary", "child_status", "tool_call_history", "duration_ms",
    ),
    "kanban_task_claimed": ("task_id", "profile_name", "board", "assignee", "run_id"),
    "kanban_task_completed": (
        "task_id", "profile_name", "board", "assignee", "run_id", "summary",
    ),
    "kanban_task_blocked": (
        "task_id", "profile_name", "board", "assignee", "run_id", "reason",
    ),
}

CORRELATION_FIELDS = {
    "session_id", "task_id", "turn_id", "tool_call_id", "api_request_id",
    "parent_session_id", "parent_turn_id", "parent_subagent_id",
    "child_session_id", "child_subagent_id", "run_id",
}


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def load_rows(bundle: str | Path) -> list[dict[str, Any]]:
    path = Path(bundle).expanduser() / RAW_NAME
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("payload"), dict):
            raise ValueError(f"invalid sanitized raw event at line {line_number}")
        rows.append(row)
    return rows


def report(bundle: str | Path) -> dict[str, Any]:
    rows = load_rows(bundle)
    by_hook: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_hook[str(row.get("hook"))].append(row["payload"])

    hook_reports = {}
    for hook, payloads in sorted(by_hook.items()):
        count = len(payloads)
        all_fields = sorted({field for payload in payloads for field in payload})
        expected = EXPECTED_FIELDS.get(hook, ())
        fields = {}
        for field in sorted(set(all_fields) | set(expected)):
            present = sum(
                1 for payload in payloads
                if field in payload and payload.get(field) not in (None, "")
            )
            types = Counter(
                _type_name(payload.get(field))
                for payload in payloads if field in payload
            )
            fields[field] = {
                "present": present,
                "total": count,
                "fraction": present / count if count else None,
                "types": dict(sorted(types.items())),
                "expected_by_current_contract": field in expected,
                "correlation_field": field in CORRELATION_FIELDS,
            }
        hook_reports[hook] = {
            "events": count,
            "expected_fields": list(expected),
            "observed_fields": all_fields,
            "missing_expected_fields_entirely": [
                field for field in expected
                if not any(field in payload and payload.get(field) not in (None, "") for payload in payloads)
            ],
            "additive_fields_not_in_checked_contract": [
                field for field in all_fields if field not in expected
            ],
            "fields": fields,
        }

    interaction_starts = by_hook.get("subagent_start", [])
    interaction_stops = by_hook.get("subagent_stop", [])
    start_sessions = {
        str(p["child_session_id"])
        for p in interaction_starts if p.get("child_session_id")
    }
    stop_sessions = {
        str(p["child_session_id"])
        for p in interaction_stops if p.get("child_session_id")
    }

    return {
        "schema": "adaptive-evolution.hook-coverage.v0.1",
        "bundle": str(Path(bundle).expanduser()),
        "events": len(rows),
        "hooks_observed": sorted(by_hook),
        "hooks_missing_from_observer_contract": sorted(set(EXPECTED_FIELDS) - set(by_hook)),
        "hooks": hook_reports,
        "identity": {
            "subagent_start_events": len(interaction_starts),
            "subagent_stop_events": len(interaction_stops),
            "start_child_sessions": len(start_sessions),
            "stop_child_sessions": len(stop_sessions),
            "stop_sessions_seen_in_start": len(stop_sessions & start_sessions),
            "stop_sessions_without_start": len(stop_sessions - start_sessions),
        },
        "authority": "contract_observation_only",
        "note": "Field coverage describes this capture only; absence does not prove the Hermes API cannot provide a field on other execution paths.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report Hermes observer hook field coverage without printing field values.")
    parser.add_argument("bundle", help="Capture bundle directory")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args(argv)
    result = report(args.bundle)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
