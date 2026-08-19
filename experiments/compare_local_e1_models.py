from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize(status: dict[str, Any], validation: dict[str, Any] | None) -> dict[str, Any]:
    counts = (validation or {}).get("counts") or {}
    checks = (validation or {}).get("checks") or {}
    return {
        "model": status.get("model"),
        "provider": status.get("provider"),
        "context_length": status.get("context_length"),
        "max_tokens": status.get("max_tokens"),
        "critical_gate_passed": bool(status.get("critical_gate_passed")),
        "hermes_run": (status.get("outcomes") or {}).get("hermes_run"),
        "repair_verify": (status.get("outcomes") or {}).get("repair_verify"),
        "e1_validation_passed": bool((validation or {}).get("passed")),
        "delegation_starts": counts.get("delegation_starts", 0),
        "delegation_stops": counts.get("delegation_stops", 0),
        "tool_errors": counts.get("tool_errors", 0),
        "tool_successes": counts.get("tool_successes", 0),
        "failure_recovery_pairs": counts.get("same_agent_failure_recovery_pairs", 0),
        "identity_clean": bool(checks.get("has_no_uncertain_session_identity", False)),
        "wall_seconds": status.get("hermes_wall_seconds"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lfm-status", type=Path, required=True)
    ap.add_argument("--lfm-validation", type=Path, required=True)
    ap.add_argument("--baseline-status", type=Path, required=True)
    ap.add_argument("--baseline-validation", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    lfm = summarize(load(args.lfm_status), load(args.lfm_validation))
    baseline = summarize(load(args.baseline_status), load(args.baseline_validation))
    same_context = lfm["context_length"] == baseline["context_length"]
    result = {
        "schema": "adaptive-evolution.local-e1-model-comparison.v0.1",
        "same_declared_context": same_context,
        "lfm": lfm,
        "baseline": baseline,
        "interpretation": {
            "lfm_passed_provider_e1": lfm["critical_gate_passed"],
            "baseline_passed_provider_e1": baseline["critical_gate_passed"],
            "quality_ranking_authorized": False,
            "reason": (
                "E1 is a runtime/tool/delegation observability gate, not a general quality benchmark. "
                "A failed model may also be confounded by provider/model-metadata/context handling."
            ),
        },
        "authority": "runtime_contract_comparison_only",
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
