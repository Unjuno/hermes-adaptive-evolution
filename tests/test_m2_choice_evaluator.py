from __future__ import annotations

from experiments.evaluate_m2_paired_choices import dominates, evaluate

TEMPLATES = {"solo", "one_leaf"}


def _records():
    common={
        "task_id":"t1","fixture_family":"fam","sequence_id":"seq","sequence_index":0,
        "split":"final_test","task_context":{"regime":"single_local_fix"},
        "repository_snapshot_id":"snap","model_id":"m","adapter_id":None,"pair_seed":1,"resource_limit_id":"lim",
        "pre_state":None,
    }
    return [
        {**common,"template":"solo","outcome":{
            "verified_success":True,"quality":0.8,"recovery_success":False,
            "terminal_failure":False,"unsafe_or_scope_violation":False,"wall_seconds":10.0,"reconfiguration_cost":0.0,
        },"post_state":{"produced_at_sequence_index":0,"source_task_ids":["t1"]}},
        {**common,"template":"one_leaf","outcome":{
            "verified_success":True,"quality":0.9,"recovery_success":False,
            "terminal_failure":False,"unsafe_or_scope_violation":False,"wall_seconds":12.0,"reconfiguration_cost":0.0,
        },"post_state":{"produced_at_sequence_index":0,"source_task_ids":["t1"]}},
    ]


def test_one_sided_unknown_blocks_dominance():
    a={"verified_success":True,"quality":1.0,"wall_seconds":5.0}
    b={"verified_success":False,"quality":0.0,"wall_seconds":None}
    assert not dominates(a,b)
    assert not dominates(b,a)


def test_pareto_evaluator_accepts_tradeoff_front():
    records=_records()
    choices=[
        {"task_id":"t1","sequence_id":"seq","sequence_index":0,"router":"fast","selected_template":"solo"},
        {"task_id":"t1","sequence_id":"seq","sequence_index":0,"router":"quality","selected_template":"one_leaf"},
    ]
    result=evaluate(records,choices,required_templates=TEMPLATES)
    assert result["passed"], result["errors"]
    assert result["routers"]["fast"]["pareto_hit_rate"] == 1.0
    assert result["routers"]["quality"]["pareto_hit_rate"] == 1.0
    assert result["routers"]["fast"]["mean_decision_score_regret"] is None


def test_explicit_decision_score_enables_scalar_regret_only_when_complete():
    records=_records()
    records[0]["outcome"]["decision_score"]=0.7
    records[1]["outcome"]["decision_score"]=0.9
    choices=[{"task_id":"t1","sequence_id":"seq","sequence_index":0,"router":"r","selected_template":"solo"}]
    result=evaluate(records,choices,required_templates=TEMPLATES)
    assert result["passed"]
    assert abs(result["routers"]["r"]["mean_decision_score_regret"] - 0.2) < 1e-12
    assert result["routers"]["r"]["scalar_regret_coverage"] == 1.0
