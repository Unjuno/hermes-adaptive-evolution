from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from run_diffusivity_proxy_falsification import (
    build_cases,
    completed_flow_gap,
    simulate_spread,
    rank_corr,
    _orient_from_root,
)
from run_completion_support_ambiguity import bridge_graph, remove_stop_for_undirected_edge


def algebraic_connectivity_fraction(adj: np.ndarray) -> float:
    """Unnormalized Laplacian lambda_2 divided by node count.

    For a fixed observed node set, adding non-negative edges adds a PSD edge
    Laplacian, so lambda_2 cannot decrease. Division by N puts K_N at 1.
    """
    a = (np.asarray(adj, dtype=float) > 0).astype(float)
    np.fill_diagonal(a, 0.0)
    n = len(a)
    if n < 2:
        return 0.0
    degree = a.sum(axis=1)
    if np.any(degree <= 0):
        return 0.0
    lap = np.diag(degree) - a
    eig = np.sort(np.real(np.linalg.eigvalsh(lap)))
    return float(np.clip(eig[1] / n, 0.0, 1.0))


def completed_binary_adjacency(starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    completed = np.minimum(starts, stops)
    return ((completed + completed.T) > 0).astype(float)


def run(seed: int, random_cases: int, replicates: int) -> dict:
    rng = np.random.default_rng(seed + 9001)
    cases = build_cases(seed, 8, random_cases)
    rows=[]
    for case in cases:
        target=simulate_spread(case.adjacency,infection_p=0.25,steps=4,replicates=replicates,rng=rng)
        rows.append({
            'name':case.name,
            'spread_fraction':target,
            'normalized_gap':completed_flow_gap(case.adjacency),
            'algebraic_fraction':algebraic_connectivity_fraction(case.adjacency),
        })
    target=[r['spread_fraction'] for r in rows]
    normalized=[r['normalized_gap'] for r in rows]
    algebraic=[r['algebraic_fraction'] for r in rows]

    adj, bridge, local = bridge_graph()
    starts=_orient_from_root(adj)
    full=starts.copy()
    support={
        'baseline':algebraic_connectivity_fraction(adj),
        'scenarios':[]
    }
    for name,edge in (('missing_bridge_return',bridge),('missing_local_return',local)):
        stops=full.copy(); remove_stop_for_undirected_edge(starts,stops,edge)
        start_active=(starts.sum(axis=0)+starts.sum(axis=1))>0
        completed_adj=completed_binary_adjacency(starts,stops)[np.ix_(start_active,start_active)]
        value=algebraic_connectivity_fraction(completed_adj)
        support['scenarios'].append({'scenario':name,'value':value,'non_increasing':value <= support['baseline'] + 1e-12})

    result={
        'schema':'adaptive-evolution.connectivity-metric-selection.v0.1',
        'seed':seed,
        'random_cases':random_cases,
        'replicates_per_start':replicates,
        'rank_correlation_with_si_spread':{
            'normalized_laplacian_gap':rank_corr(normalized,target),
            'algebraic_connectivity_fraction':rank_corr(algebraic,target),
        },
        'missing_return_monotonicity':support,
        'conclusion':{},
        'rows':rows,
        'authority':'synthetic_metric_selection_only',
    }
    alg_corr=result['rank_correlation_with_si_spread']['algebraic_connectivity_fraction']
    monotone=all(s['non_increasing'] for s in support['scenarios'])
    result['conclusion']={
        'algebraic_candidate_supported':bool(alg_corr>0.65 and monotone),
        'monotone_under_tested_missing_returns':monotone,
        'note':(
            'Selection requires both decision-relevant correlation and conservative evidence semantics. '
            'No synthetic metric becomes routing authority without real-task validation.'
        )
    }
    return result


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed',type=int,default=31)
    ap.add_argument('--random-cases',type=int,default=80)
    ap.add_argument('--replicates',type=int,default=100)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    result=run(args.seed,args.random_cases,args.replicates)
    text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
    print(text,end='')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
