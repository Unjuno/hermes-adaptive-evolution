from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path
from typing import Any

import numpy as np

ROLES = ("research", "implementation", "verification", "coordination")


def posterior(counts: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    values = counts + alpha
    return values / values.sum(axis=-1, keepdims=True)


def js_divergence(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    m = 0.5 * (p + q)
    eps = 1e-12
    return 0.5 * np.sum(p * np.log((p + eps) / (m + eps)), axis=1) + 0.5 * np.sum(q * np.log((q + eps) / (m + eps)), axis=1)


def generate(seed: int, agents: int, steps: int, change_at: int, changed_fraction: float, noise: float):
    rng = np.random.default_rng(seed)
    initial = np.arange(agents) % len(ROLES)
    rng.shuffle(initial)
    changed_n = max(1, int(round(agents * changed_fraction)))
    changed_idx = np.sort(rng.choice(agents, size=changed_n, replace=False))
    post = initial.copy()
    shifts = rng.integers(1, len(ROLES), size=changed_n)
    post[changed_idx] = (post[changed_idx] + shifts) % len(ROLES)

    true_roles = np.repeat(initial[None, :], steps, axis=0)
    true_roles[change_at:, :] = post
    emissions = np.empty((steps, agents), dtype=int)
    for t in range(steps):
        truth = true_roles[t]
        correct = rng.random(agents) >= noise
        emissions[t] = truth
        wrong_agents = np.flatnonzero(~correct)
        if wrong_agents.size:
            offset = rng.integers(1, len(ROLES), size=wrong_agents.size)
            emissions[t, wrong_agents] = (truth[wrong_agents] + offset) % len(ROLES)
    stable_idx = np.array([i for i in range(agents) if i not in set(changed_idx)], dtype=int)
    return true_roles, emissions, changed_idx, stable_idx


def evaluate_probs(probs: np.ndarray, truth: np.ndarray, changed_idx: np.ndarray, stable_idx: np.ndarray, change_at: int) -> dict[str, Any]:
    pred = probs.argmax(axis=2)
    correct = pred == truth
    eps = 1e-12
    nll = -np.log(np.take_along_axis(probs, truth[:, :, None], axis=2).squeeze(2) + eps)

    pre_slice = slice(max(0, change_at - 80), change_at)
    late_slice = slice(min(len(truth), change_at + 80), len(truth))
    changed_accuracy = correct[:, changed_idx].mean(axis=1)

    recovery = None
    window = 5
    for t in range(change_at, len(truth) - window + 1):
        if float(changed_accuracy[t:t + window].mean()) >= 0.90:
            recovery = t - change_at
            break

    return {
        "pre_change_accuracy": float(correct[pre_slice].mean()),
        "pre_change_nll": float(nll[pre_slice].mean()),
        "changed_accuracy_first20": float(correct[change_at:min(len(truth), change_at + 20), changed_idx].mean()),
        "changed_accuracy_late": float(correct[late_slice, changed_idx].mean()) if late_slice.start < len(truth) else None,
        "stable_accuracy_after_change": float(correct[change_at:, stable_idx].mean()) if stable_idx.size else None,
        "post_change_nll": float(nll[change_at:].mean()),
        "recovery_latency_to_90pct_5round_mean": recovery,
        "never_recovered": recovery is None,
    }


def infer_methods(emissions: np.ndarray) -> dict[str, np.ndarray]:
    steps, agents = emissions.shape
    roles = len(ROLES)
    methods: dict[str, np.ndarray] = {}

    # Lifetime memory.
    counts = np.zeros((agents, roles), dtype=float)
    out = np.zeros((steps, agents, roles), dtype=float)
    for t in range(steps):
        counts[np.arange(agents), emissions[t]] += 1.0
        out[t] = posterior(counts)
    methods["lifetime"] = out

    # Rolling windows.
    for width in (20, 50, 100):
        counts = np.zeros((agents, roles), dtype=float)
        queues = [deque() for _ in range(agents)]
        out = np.zeros((steps, agents, roles), dtype=float)
        for t in range(steps):
            for a in range(agents):
                r = int(emissions[t, a])
                queues[a].append(r)
                counts[a, r] += 1.0
                if len(queues[a]) > width:
                    old = queues[a].popleft()
                    counts[a, old] -= 1.0
            out[t] = posterior(counts)
        methods[f"rolling_{width}"] = out

    # Exponential memories.
    exp_outputs: dict[int, np.ndarray] = {}
    for half_life in (20, 50, 100):
        decay = math.exp(-math.log(2.0) / half_life)
        counts = np.zeros((agents, roles), dtype=float)
        out = np.zeros((steps, agents, roles), dtype=float)
        for t in range(steps):
            counts *= decay
            counts[np.arange(agents), emissions[t]] += 1.0
            out[t] = posterior(counts)
        methods[f"exp_{half_life}"] = out
        exp_outputs[half_life] = out

    # Two-timescale adaptive memory. The threshold is a model-selection axis,
    # not a production constant.
    fast = exp_outputs[20]
    slow = exp_outputs[100]
    for threshold in (0.05, 0.10, 0.20):
        out = np.zeros_like(fast)
        for t in range(steps):
            divergence = js_divergence(fast[t], slow[t])
            use_fast = divergence > threshold
            out[t] = slow[t]
            out[t, use_fast] = fast[t, use_fast]
        methods[f"adaptive_js_{threshold:.2f}"] = out

    return methods


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, str], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((float(row["noise"]), str(row["method"])), []).append(row)
    out=[]
    metric_names = (
        "pre_change_accuracy", "pre_change_nll", "changed_accuracy_first20",
        "changed_accuracy_late", "stable_accuracy_after_change", "post_change_nll",
        "recovery_latency_to_90pct_5round_mean",
    )
    for (noise, method), values in sorted(groups.items()):
        metrics={}
        for name in metric_names:
            observed=[float(v[name]) for v in values if v.get(name) is not None]
            metrics[name]={
                "mean": float(np.mean(observed)) if observed else None,
                "median": float(np.median(observed)) if observed else None,
            }
        metrics["never_recovered_rate"] = sum(bool(v["never_recovered"]) for v in values) / len(values)
        out.append({"noise":noise,"method":method,"runs":len(values),"metrics":metrics})
    return out


def run(seeds: list[int], agents: int, steps: int, change_at: int, changed_fraction: float, noises: list[float]) -> dict[str, Any]:
    rows=[]
    for noise in noises:
        for seed in seeds:
            truth, emissions, changed, stable = generate(seed, agents, steps, change_at, changed_fraction, noise)
            for method, probs in infer_methods(emissions).items():
                metrics=evaluate_probs(probs,truth,changed,stable,change_at)
                rows.append({"seed":seed,"noise":noise,"method":method,**metrics})
    agg=aggregate(rows)

    # Report the empirical Pareto set per noise over three primary tradeoffs:
    # pre-change accuracy ↑, recovery latency ↓, stable accuracy after change ↑.
    pareto={}
    for noise in noises:
        candidates=[x for x in agg if float(x["noise"]) == float(noise)]
        front=[]
        for a in candidates:
            am=a["metrics"]
            a_vals=(
                am["pre_change_accuracy"]["mean"],
                am["recovery_latency_to_90pct_5round_mean"]["mean"],
                am["stable_accuracy_after_change"]["mean"],
            )
            dominated=False
            for b in candidates:
                if b is a: continue
                bm=b["metrics"]
                b_vals=(
                    bm["pre_change_accuracy"]["mean"],
                    bm["recovery_latency_to_90pct_5round_mean"]["mean"],
                    bm["stable_accuracy_after_change"]["mean"],
                )
                if None in a_vals or None in b_vals: continue
                no_worse=(b_vals[0] >= a_vals[0] and b_vals[1] <= a_vals[1] and b_vals[2] >= a_vals[2])
                strict=(b_vals[0] > a_vals[0] or b_vals[1] < a_vals[1] or b_vals[2] > a_vals[2])
                if no_worse and strict:
                    dominated=True; break
            if not dominated: front.append(a["method"])
        pareto[str(noise)] = sorted(front)

    return {
        "schema":"adaptive-evolution.role-memory-selection.v0.1",
        "configuration":{
            "agents":agents,"steps":steps,"change_at":change_at,"changed_fraction":changed_fraction,
            "roles":list(ROLES),"noises":noises,"seeds":seeds,
        },
        "aggregate":agg,
        "pareto_methods":pareto,
        "rows":rows,
        "authority":"synthetic_role_memory_falsification_only",
        "note":(
            "This experiment selects memory behavior, not a production window constant. "
            "Role timing must later be calibrated on real Hermes tool/action histories."
        ),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--seeds",nargs="*",type=int,default=[11,23,37,53,71,89,107,131])
    ap.add_argument("--agents",type=int,default=60)
    ap.add_argument("--steps",type=int,default=400)
    ap.add_argument("--change-at",type=int,default=200)
    ap.add_argument("--changed-fraction",type=float,default=0.30)
    ap.add_argument("--noises",nargs="*",type=float,default=[0.10,0.30,0.50])
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    result=run(args.seeds,args.agents,args.steps,args.change_at,args.changed_fraction,args.noises)
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
    print(text,end="")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
