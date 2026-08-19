from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adaptive_evolution_observer.bundle import replay_bundle

NORMALIZED_NAME = "normalized-events.jsonl"
MANIFEST_NAME = "manifest.json"
SUCCESS_STATUSES = frozenset({"ok", "success"})
FAILURE_STATUSES = frozenset({"error", "failed", "blocked", "cancelled", "canceled"})


def _load_events(bundle: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate((bundle / NORMALIZED_NAME).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"normalized event at line {line_number} is not an object")
        rows.append(row)
    return rows


def _tool_status(event: dict[str, Any]) -> str:
    return str((event.get("data") or {}).get("status") or "").strip().lower()


def validate(bundle: str | Path) -> dict[str, Any]:
    root = Path(bundle).expanduser()
    replay = replay_bundle(root)
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    events = _load_events(root)

    starts = [event for event in events if event.get("kind") == "interaction_start"]
    stops = [event for event in events if event.get("kind") == "interaction_stop"]
    tool_events = [event for event in events if event.get("kind") == "tool_result"]
    errors = [
        event for event in tool_events
        if _tool_status(event) in FAILURE_STATUSES
        or (event.get("data") or {}).get("error_type")
    ]
    successes = [
        event for event in tool_events
        if _tool_status(event) in SUCCESS_STATUSES
        and not (event.get("data") or {}).get("error_type")
    ]

    recovered_pairs = []
    for failure in errors:
        failure_agent = failure.get("agent_id")
        failure_seq = int(failure.get("seq") or 0)
        later = [
            success for success in successes
            if success.get("agent_id") == failure_agent
            and int(success.get("seq") or 0) > failure_seq
        ]
        if later:
            recovered_pairs.append({
                "agent_id": failure_agent,
                "failure_seq": failure_seq,
                "recovery_seq": int(later[0].get("seq") or 0),
            })

    checks = {
        "bundle_replay_matches": bool(
            replay.get("normalization_matches_trace")
            and replay.get("matches_manifest_state")
        ),
        "privacy_content_capture_disabled": not bool(
            (manifest.get("privacy") or {}).get("capture_content")
        ),
        "has_delegation_start": bool(starts),
        "has_delegation_stop": bool(stops),
        "has_tool_error": bool(errors),
        "has_later_same_agent_tool_success": bool(recovered_pairs),
        "has_no_uncertain_session_identity": int(
            (replay.get("event_diagnostics") or {}).get("uncertain_session_events") or 0
        ) == 0,
        "has_interaction_state": int((replay.get("state") or {}).get("interaction_events") or 0) >= 1,
    }
    passed = all(checks.values())
    return {
        "schema": "adaptive-evolution.e1-validation.v0.1",
        "bundle": str(root),
        "passed": passed,
        "checks": checks,
        "counts": {
            "normalized_events": len(events),
            "delegation_starts": len(starts),
            "delegation_stops": len(stops),
            "tool_errors": len(errors),
            "tool_successes": len(successes),
            "same_agent_failure_recovery_pairs": len(recovered_pairs),
        },
        "recognized_tool_statuses": {
            "success": sorted(SUCCESS_STATUSES),
            "failure": sorted(FAILURE_STATUSES),
        },
        "recovered_pairs": recovered_pairs,
        "runtime": manifest.get("runtime"),
        "authority": "e1_contract_gate_only",
        "note": "Passing E1 proves a provider-backed observability path, not that organization-state variables improve decisions.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a provider-backed E1 Hermes capture bundle.")
    parser.add_argument("bundle")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    result = validate(args.bundle)
    encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
