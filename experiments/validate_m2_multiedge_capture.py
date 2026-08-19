from __future__ import annotations

import argparse
import json
from pathlib import Path

from adaptive_evolution_observer.estimator import estimate
from adaptive_evolution_observer.normalizer import normalize

RAW_NAME = "sanitized-raw-events.jsonl"
EXPECTED_CONNECTIVITY_METHOD = "unnormalized_algebraic_lambda2_over_n_binary_completed_relations"


def load_raw(bundle: Path) -> list[dict]:
    rows=[]
    for line in (bundle / RAW_NAME).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    if not rows:
        raise ValueError("capture has no sanitized raw events")
    return rows


def validate(bundle: Path) -> dict:
    raw=load_raw(bundle)
    events, diagnostics=normalize(raw)
    state=estimate(events)
    checks={
        "schema_v04": state.get("schema") == "adaptive-evolution.organization-state.v0.4",
        "connectivity_method_v04": state.get("completed_flow_connectivity_method") == EXPECTED_CONNECTIVITY_METHOD,
        "at_least_three_agents": int(state.get("agents") or 0) >= 3,
        "at_least_two_interactions": int(state.get("interaction_events") or 0) >= 2,
        "at_least_two_completed_interactions": int(state.get("completed_interaction_events") or 0) >= 2,
        "completion_coverage_present": state.get("interaction_completion_coverage") is not None,
        "traffic_breadth_present": state.get("directed_traffic_breadth") is not None,
        "completed_flow_connectivity_present": state.get("completed_flow_connectivity") is not None,
        "no_uncertain_identity": int(diagnostics.get("uncertain_session_events") or 0) == 0,
        "legacy_gap_deauthorized": state.get("directed_diffusivity_authority") == "deprecated_diagnostic_only",
    }
    passed=all(checks.values())
    return {
        "schema":"adaptive-evolution.m2-multiedge-validation.v0.2",
        "bundle":str(bundle),
        "passed":passed,
        "checks":checks,
        "event_diagnostics":diagnostics,
        "organization_state":state,
        "authority":"m2_observability_contract_only",
        "note":(
            "Passing proves that a real Hermes multi-edge trajectory exposes the v0.4 vector topology state. "
            "It does not prove that these observables improve routing decisions."
        ),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("bundle",type=Path)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=validate(args.bundle)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
