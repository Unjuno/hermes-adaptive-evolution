from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .validate_m2_benchmark_records import load_jsonl, validate_records
except ImportError:  # direct `python experiments/...py` execution
    from validate_m2_benchmark_records import load_jsonl, validate_records

MAXIMIZE = ("verified_success", "quality", "recovery_success")
MINIMIZE = ("terminal_failure", "unsafe_or_scope_violation", "wall_seconds", "reconfiguration_cost")


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dominates(a: dict[str, Any], b: dict[str, Any], epsilon: dict[str, float] | None = None) -> bool:
    """Conservative Pareto dominance: one-sided unknowns block dominance.

    If a dimension is known for only one candidate, either value could reverse
    the ordering, so neither candidate may claim dominance through the remaining
    dimensions. Dimensions missing for both candidates are ignored. At least one
    mutually known dimension must improve beyond epsilon and none may be worse.
    """
    epsilon = epsilon or {}
    compared = 0
    strict = False
    for name in MAXIMIZE:
        av, bv = _number(a.get(name)), _number(b.get(name))
        if (av is None) != (bv is None):
            return False
        if av is None:
            continue
        compared += 1
        e = float(epsilon.get(name, 0.0))
        if av < bv - e:
            return False
        if av > bv + e:
            strict = True
    for name in MINIMIZE:
        av, bv = _number(a.get(name)), _number(b.get(name))
        if (av is None) != (bv is None):
            return False
        if av is None:
            continue
        compared += 1
        e = float(epsilon.get(name, 0.0))
        if av > bv + e:
            return False
        if av < bv - e:
            strict = True
    return compared > 0 and strict


def pareto_front(group: list[dict[str, Any]], epsilon: dict[str, float] | None = None) -> set[str]:
    front: set[str] = set()
    for row in group:
        template = str(row["template"])
        outcome = row.get("outcome") or {}
        if not any(dominates(other.get("outcome") or {}, outcome, epsilon) for other in group if other is not row):
            front.add(template)
    return front


def load_choices(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"choice line {lineno}: expected object")
        row["_line"] = lineno
        rows.append(row)
    if not rows:
        raise ValueError("choice file is empty")
    return rows


def evaluate(
    records: list[dict[str, Any]],
    choices: list[dict[str, Any]],
    *,
    required_templates: set[str] | None = None,
    epsilon: dict[str, float] | None = None,
) -> dict[str, Any]:
    integrity = validate_records(records, required_templates=required_templates)
    if not integrity["passed"]:
        return {
            "schema": "adaptive-evolution.m2-choice-evaluation.v0.1",
            "passed": False,
            "integrity": integrity,
            "errors": ["benchmark integrity gate failed"],
            "authority": "routing_evaluation",
        }

    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        groups[(str(row["task_id"]), str(row["sequence_id"]), int(row["sequence_index"]))].append(row)

    errors: list[str] = []
    by_router: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_choice_keys: set[tuple[str, str, int, str]] = set()

    for choice in choices:
        try:
            key = (str(choice["task_id"]), str(choice["sequence_id"]), int(choice["sequence_index"]))
            router = str(choice["router"])
            selected = str(choice["selected_template"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid choice line {choice.get('_line')}: {exc}")
            continue
        unique = (*key, router)
        if unique in seen_choice_keys:
            errors.append(f"duplicate choice for group={key} router={router}")
            continue
        seen_choice_keys.add(unique)
        group = groups.get(key)
        if not group:
            errors.append(f"choice references unknown paired group {key}")
            continue
        rows_by_template = {str(r["template"]): r for r in group}
        if selected not in rows_by_template:
            errors.append(f"router {router} selected unavailable template {selected!r} for group {key}")
            continue
        front = pareto_front(group, epsilon)
        row = rows_by_template[selected]
        outcome = row.get("outcome") or {}
        scores = [_number((r.get("outcome") or {}).get("decision_score")) for r in group]
        selected_score = _number(outcome.get("decision_score"))
        scalar_regret = None
        if selected_score is not None and all(s is not None for s in scores):
            scalar_regret = max(float(s) for s in scores if s is not None) - selected_score
        by_router[router].append({
            "group": list(key),
            "selected_template": selected,
            "pareto_front": sorted(front),
            "pareto_hit": selected in front,
            "verified_success": bool(outcome.get("verified_success")) if outcome.get("verified_success") is not None else None,
            "terminal_failure": bool(outcome.get("terminal_failure")) if outcome.get("terminal_failure") is not None else None,
            "unsafe_or_scope_violation": bool(outcome.get("unsafe_or_scope_violation")) if outcome.get("unsafe_or_scope_violation") is not None else None,
            "wall_seconds": _number(outcome.get("wall_seconds")),
            "decision_score_regret": scalar_regret,
        })

    summaries = {}
    for router, rows in sorted(by_router.items()):
        n = len(rows)
        pareto_hits = [r["pareto_hit"] for r in rows]
        success = [r["verified_success"] for r in rows if r["verified_success"] is not None]
        terminal = [r["terminal_failure"] for r in rows if r["terminal_failure"] is not None]
        unsafe = [r["unsafe_or_scope_violation"] for r in rows if r["unsafe_or_scope_violation"] is not None]
        wall = [r["wall_seconds"] for r in rows if r["wall_seconds"] is not None]
        regret = [r["decision_score_regret"] for r in rows if r["decision_score_regret"] is not None]
        summaries[router] = {
            "choices": n,
            "pareto_hit_rate": sum(bool(x) for x in pareto_hits) / n if n else None,
            "verified_success_rate": sum(bool(x) for x in success) / len(success) if success else None,
            "terminal_failure_rate": sum(bool(x) for x in terminal) / len(terminal) if terminal else None,
            "unsafe_or_scope_violation_rate": sum(bool(x) for x in unsafe) / len(unsafe) if unsafe else None,
            "mean_wall_seconds": sum(float(x) for x in wall) / len(wall) if wall else None,
            "mean_decision_score_regret": sum(float(x) for x in regret) / len(regret) if regret else None,
            "scalar_regret_coverage": len(regret) / n if n else 0.0,
        }

    return {
        "schema": "adaptive-evolution.m2-choice-evaluation.v0.1",
        "passed": not errors,
        "integrity": integrity,
        "errors": errors,
        "epsilon": epsilon or {},
        "routers": summaries,
        "details": dict(by_router),
        "authority": "routing_evaluation",
        "note": (
            "Pareto hit rate does not invent utility weights. One-sided unknown metrics block dominance. "
            "Scalar regret is reported only where every candidate in a paired group carries an explicitly supplied "
            "outcome.decision_score."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("choices", type=Path)
    ap.add_argument("--templates", nargs="*", default=None)
    ap.add_argument("--epsilon-json", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    epsilon = json.loads(args.epsilon_json.read_text()) if args.epsilon_json else None
    result = evaluate(
        load_jsonl(args.records),
        load_choices(args.choices),
        required_templates=None if args.templates is None else set(args.templates),
        epsilon=epsilon,
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
