from __future__ import annotations

from copy import deepcopy

from experiments.validate_m2_benchmark_records import validate_records

TEMPLATES = {"solo", "one_leaf", "two_leaf_serial", "implement_then_review"}


def _records():
    rows=[]
    for template in sorted(TEMPLATES):
        rows.append({
            "task_id":"task-a",
            "fixture_family":"family-a",
            "sequence_id":"seq-train",
            "sequence_index":1,
            "split":"discovery",
            "task_context":{"regime":"diagnose_then_fix"},
            "template":template,
            "repository_snapshot_id":"snap-1",
            "model_id":"model-1",
            "adapter_id":None,
            "pair_seed":7,
            "resource_limit_id":"limit-1",
            "pre_state":{
                "as_of_sequence_index":0,
                "source_task_ids":["task-prev"],
                "directed_traffic_breadth":0.5,
            },
            "outcome":{"verified_success":True},
            "post_state":{
                "produced_at_sequence_index":1,
                "source_task_ids":["task-a"],
            },
            "router_features":["task_context","pre_state.directed_traffic_breadth"],
        })
    return rows


def test_valid_paired_records_pass():
    result=validate_records(_records(),required_templates=TEMPLATES)
    assert result["passed"], result["errors"]
    assert result["paired_groups"] == 1


def test_same_task_post_state_cannot_become_pre_state():
    rows=_records()
    rows[0]["pre_state"]["source_task_ids"]=["task-a"]
    result=validate_records(rows,required_templates=TEMPLATES)
    assert not result["passed"]
    assert any(e["code"] == "same_task_state_leak" for e in result["errors"])


def test_future_pre_state_is_rejected():
    rows=_records()
    rows[0]["pre_state"]["as_of_sequence_index"]=1
    result=validate_records(rows,required_templates=TEMPLATES)
    assert not result["passed"]
    assert any(e["code"] == "future_state_leak" for e in result["errors"])


def test_fixture_family_cannot_cross_splits():
    rows=_records()
    extra=deepcopy(rows[0])
    extra.update({
        "task_id":"task-final",
        "sequence_id":"seq-final",
        "sequence_index":0,
        "split":"final_test",
        "template":"solo",
        "pre_state":None,
        "post_state":{"produced_at_sequence_index":0,"source_task_ids":["task-final"]},
    })
    rows.append(extra)
    result=validate_records(rows)
    assert not result["passed"]
    assert any(e["code"] == "fixture_family_split_leak" for e in result["errors"])


def test_pair_invariant_mismatch_is_rejected():
    rows=_records()
    rows[0]["pair_seed"]=99
    result=validate_records(rows,required_templates=TEMPLATES)
    assert not result["passed"]
    assert any(e["code"] == "pair_invariant_mismatch" for e in result["errors"])


def test_legacy_diffusivity_feature_is_forbidden():
    rows=_records()
    rows[0]["router_features"].append("directed_diffusivity")
    result=validate_records(rows,required_templates=TEMPLATES)
    assert not result["passed"]
    assert any(e["code"] == "forbidden_router_feature" for e in result["errors"])
