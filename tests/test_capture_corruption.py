from __future__ import annotations

from pathlib import Path

from adaptive_evolution_observer.bundle import create_bundle
from adaptive_evolution_observer.store import EventStore
from experiments.run_capture_corruption import run


def _bundle(tmp_path: Path) -> Path:
    db = tmp_path / "observer.sqlite3"
    store = EventStore(db)
    store.append("on_session_start", {"session_id": "root", "platform": "cli"})
    for i in range(5):
        store.append("post_tool_call", {
            "session_id": "root",
            "task_id": "task-root",
            "turn_id": f"rt-{i}",
            "tool_call_id": f"root-tc-{i}",
            "tool_name": "terminal",
            "status": "success",
        })
    store.append("subagent_start", {
        "parent_session_id": "root",
        "parent_turn_id": "t1",
        "child_session_id": "child",
        "child_subagent_id": "sub1",
        "child_role": "leaf",
    })
    for i in range(20):
        store.append("post_tool_call", {
            "session_id": "child",
            "task_id": "task-child",
            "turn_id": f"ct-{i}",
            "tool_call_id": f"tc-{i}",
            "tool_name": "python" if i % 2 else "web_search",
            "status": "error" if i in {4, 9} else "success",
            "error_type": "fixture" if i in {4, 9} else None,
        })
    store.append("subagent_stop", {
        "parent_session_id": "root",
        "parent_turn_id": "t1",
        "child_session_id": "child",
        "child_role": "leaf",
        "child_status": "completed",
    })
    target = tmp_path / "bundle"
    create_bundle(db, target)
    return target


def _group(result, scenario: str, rate: float):
    return next(
        group for group in result["summary"]["groups"]
        if group["scenario"] == scenario and group["rate"] == rate
    )


def test_full_reorder_is_semantically_invariant(tmp_path: Path):
    result = run(_bundle(tmp_path), replicates=5, seed=7)
    group = _group(result, "full_reorder", 1.0)
    assert group["metrics"]["normalized_count_ratio"]["median"] == 1.0
    assert group["metrics"]["interaction_event_delta"]["max"] == 0.0
    assert group["metrics"]["tool_outcome_delta"]["max"] == 0.0
    assert group["metrics"]["role_mixing_abs_error"]["max"] == 0.0
    assert group["metrics"]["role_conditioned_traffic_coverage_abs_error"]["max"] == 0.0


def test_duplicate_experiment_reports_deduplicated_state(tmp_path: Path):
    result = run(_bundle(tmp_path), replicates=5, seed=8)
    group = _group(result, "duplicate", 0.10)
    assert group["replicates"] == 5
    # Strong-ID Hermes observer events should usually deduplicate back to the
    # baseline normalized count even when the raw portable stream is duplicated.
    assert group["metrics"]["normalized_count_ratio"]["median"] == 1.0


def test_drop_experiment_exposes_state_damage_without_thresholds(tmp_path: Path):
    result = run(_bundle(tmp_path), replicates=4, seed=9)
    group = _group(result, "drop", 0.10)
    assert group["metrics"]["normalized_count_ratio"]["median"] < 1.0
    assert result["authority"] == "experiment_only"
    assert "production activation threshold" in result["note"]
