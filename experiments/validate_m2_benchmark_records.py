from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ALLOWED_SPLITS = {"discovery", "selection", "final_test"}
PAIR_INVARIANT_FIELDS = (
    "repository_snapshot_id",
    "model_id",
    "adapter_id",
    "pair_seed",
    "resource_limit_id",
)
FORBIDDEN_ROUTER_FEATURES = {
    "directed_diffusivity",
    "same_task_post_state",
    "final_test_future_state",
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"line {lineno}: record must be an object")
        value["_line"] = lineno
        rows.append(value)
    if not rows:
        raise ValueError("benchmark record file is empty")
    return rows


def _error(errors: list[dict[str, Any]], row: dict[str, Any] | None, code: str, message: str) -> None:
    errors.append({
        "line": None if row is None else row.get("_line"),
        "task_id": None if row is None else row.get("task_id"),
        "code": code,
        "message": message,
    })


def _state_sources(state: Any) -> set[str]:
    if not isinstance(state, dict):
        return set()
    values = state.get("source_task_ids") or []
    if isinstance(values, str):
        values = [values]
    return {str(v) for v in values if v not in (None, "")}


def validate_records(
    rows: Iterable[dict[str, Any]],
    *,
    required_templates: set[str] | None = None,
) -> dict[str, Any]:
    rows = [dict(r) for r in rows]
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required = {
        "task_id", "fixture_family", "sequence_id", "sequence_index",
        "split", "task_context", "template", "pre_state", "outcome", "post_state",
    }

    family_splits: dict[str, set[str]] = defaultdict(set)
    sequence_splits: dict[str, set[str]] = defaultdict(set)
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        missing = sorted(required - set(row))
        if missing:
            _error(errors, row, "missing_fields", f"missing required fields: {missing}")
            continue
        split = str(row.get("split"))
        if split not in ALLOWED_SPLITS:
            _error(errors, row, "invalid_split", f"invalid split {split!r}")
        family = str(row.get("fixture_family"))
        sequence_id = str(row.get("sequence_id"))
        try:
            sequence_index = int(row.get("sequence_index"))
        except (TypeError, ValueError):
            _error(errors, row, "invalid_sequence_index", "sequence_index must be an integer")
            continue
        if sequence_index < 0:
            _error(errors, row, "invalid_sequence_index", "sequence_index must be >= 0")

        family_splits[family].add(split)
        sequence_splits[sequence_id].add(split)
        groups[(str(row.get("task_id")), sequence_id, sequence_index)].append(row)

        task_id = str(row.get("task_id"))
        pre_state = row.get("pre_state")
        post_state = row.get("post_state")

        if pre_state is not None and not isinstance(pre_state, dict):
            _error(errors, row, "invalid_pre_state", "pre_state must be null or an object")
        if post_state is not None and not isinstance(post_state, dict):
            _error(errors, row, "invalid_post_state", "post_state must be null or an object")

        if isinstance(pre_state, dict):
            if task_id in _state_sources(pre_state):
                _error(errors, row, "same_task_state_leak", "pre_state contains current task_id in source_task_ids")
            as_of = pre_state.get("as_of_sequence_index")
            if as_of is not None:
                try:
                    as_of_int = int(as_of)
                    if as_of_int >= sequence_index:
                        _error(
                            errors, row, "future_state_leak",
                            f"pre_state as_of_sequence_index={as_of_int} must be < current index {sequence_index}",
                        )
                except (TypeError, ValueError):
                    _error(errors, row, "invalid_pre_state_index", "pre_state.as_of_sequence_index must be integer/null")

        if isinstance(post_state, dict):
            produced = post_state.get("produced_at_sequence_index")
            if produced is not None:
                try:
                    if int(produced) != sequence_index:
                        _error(
                            errors, row, "post_state_time_mismatch",
                            f"post_state produced_at_sequence_index={produced!r} != {sequence_index}",
                        )
                except (TypeError, ValueError):
                    _error(errors, row, "invalid_post_state_index", "post_state.produced_at_sequence_index must be integer/null")
            sources = _state_sources(post_state)
            if sources and task_id not in sources:
                _error(errors, row, "post_state_source_mismatch", "post_state source_task_ids does not include current task")

        router_features = row.get("router_features") or []
        if isinstance(router_features, str):
            router_features = [router_features]
        forbidden = sorted(FORBIDDEN_ROUTER_FEATURES & {str(x) for x in router_features})
        if forbidden:
            _error(errors, row, "forbidden_router_feature", f"forbidden router features: {forbidden}")

    for family, splits in sorted(family_splits.items()):
        if len(splits) > 1:
            _error(errors, None, "fixture_family_split_leak", f"fixture_family {family!r} spans splits {sorted(splits)}")
    for sequence_id, splits in sorted(sequence_splits.items()):
        if len(splits) > 1:
            _error(errors, None, "sequence_split_leak", f"sequence_id {sequence_id!r} spans splits {sorted(splits)}")

    for key, candidates in sorted(groups.items()):
        templates = [str(r.get("template")) for r in candidates]
        if len(templates) != len(set(templates)):
            for row in candidates:
                _error(errors, row, "duplicate_template", f"duplicate template within paired task group {key}")
        if required_templates is not None:
            missing_templates = sorted(required_templates - set(templates))
            extra_templates = sorted(set(templates) - required_templates)
            if missing_templates or extra_templates:
                for row in candidates:
                    _error(
                        errors, row, "incomplete_pair",
                        f"paired group {key} missing={missing_templates} extra={extra_templates}",
                    )

        contexts = {json.dumps(r.get("task_context"), sort_keys=True, separators=(",", ":")) for r in candidates}
        if len(contexts) > 1:
            for row in candidates:
                _error(errors, row, "pair_context_mismatch", f"task_context differs within paired group {key}")

        for field in PAIR_INVARIANT_FIELDS:
            values = {json.dumps(r.get(field), sort_keys=True, default=str) for r in candidates if field in r}
            if len(values) > 1:
                for row in candidates:
                    _error(errors, row, "pair_invariant_mismatch", f"{field} differs within paired group {key}")
            if not values:
                warnings.append({
                    "group": list(key),
                    "code": "pair_invariant_unrecorded",
                    "field": field,
                    "message": f"{field} is not recorded; pairing cannot be audited for this dimension",
                })

    return {
        "schema": "adaptive-evolution.m2-benchmark-validation.v0.1",
        "records": len(rows),
        "paired_groups": len(groups),
        "fixture_families": len(family_splits),
        "sequences": len(sequence_splits),
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
        "authority": "benchmark_integrity_gate",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate M2 benchmark pairing, split isolation, and temporal causality.")
    ap.add_argument("records", type=Path)
    ap.add_argument("--templates", nargs="*", default=None)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = validate_records(
        load_jsonl(args.records),
        required_templates=None if args.templates is None else set(args.templates),
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
