"""Registered-task effects, outcome-dependent stopping and missingness.
Synthetic paired worlds only; no provider calls or action authorization.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, platform, sys, time
from pathlib import Path
from statistics import NormalDist
import numpy as np

BETS = np.array([0., .02, .05, .1, .2, .4, .8])
ALPHA = .05
SEED = 2026090817

def wilson(k: int, n: int) -> list[float]:
    z = NormalDist().inv_cdf(.975)
    p = k/n; den = 1+z*z/n
    c = (p+z*z/(2*n))/den
    h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0., c-h), min(1., c+h)]

def process(x: np.ndarray, include: np.ndarray | None = None) -> dict:
    """Same prespecified mixture as prior evidence_gate; optional row deletion is a bad baseline."""
    nr, nt = x.shape
    logs = np.zeros((nr, len(BETS)))
    cross = np.zeros(nr, dtype=bool)
    first = np.full(nr, nt, dtype=int)
    maxlog = np.zeros(nr)
    counts = np.zeros(nr, dtype=int)
    for i in range(nt):
        mask = np.ones(nr, dtype=bool) if include is None else include[:,i]
        logs[mask] += np.log1p(x[mask,i,None]*BETS)
        counts += mask
        val = np.logaddexp.reduce(logs, axis=1)-math.log(len(BETS))
        maxlog = np.maximum(maxlog,val)
        hit = val >= -math.log(ALPHA)
        first[hit & ~cross] = i+1
        cross |= hit
    terminal = val >= -math.log(ALPHA)
    denom = counts if include is not None else np.full(nr, nt)
    means = np.sum(x if include is None else np.where(include,x,0.),axis=1)/np.maximum(denom,1)
    return {'cross':cross,'terminal':terminal,'first':first,'mean':means,'count':counts,'maxlog':maxlog}

def summary(r: dict) -> dict:
    n = len(r['cross']); k = int(r['cross'].sum())
    return {'crossings':k,'replications':n,'crossing_rate':k/n,'wilson95':wilson(k,n),
            'terminal_positive':int(r['terminal'].sum()),'mean_contribution':float(r['mean'].mean()),
            'se_mean_across_worlds':float(r['mean'].std(ddof=1)/math.sqrt(n)),
            'median_units_to_cross_or_cap':float(np.median(r['first'])),
            'median_included_units':float(np.median(r['count']))}

def analyze(reps: int, tasks: int, seed: int) -> tuple[dict, dict]:
    output = {}; arrays = {}
    rng = np.random.default_rng(np.random.SeedSequence([seed,1]))
    x = np.where(rng.random((reps,tasks,2)) < .5, 1., -1.)
    # Stop after a favorable first replicate; otherwise collect the second.
    used = np.where(x[:,:,0]>0,1,2)
    stopmean = np.where(used==1, x[:,:,0], x.mean(axis=2))
    protocols = {'first_attempt':x[:,:,0], 'fixed_two_mean':x.mean(axis=2),
                 'stop_when_first_positive_mean':stopmean,
                 'stopped_sum_fixed_denominator_2':stopmean*used/2.}
    rr = {}
    for name,vals in protocols.items():
        p = process(vals); rr[name]=summary(p)
        for k,v in p.items(): arrays['retry_'+name+'_'+k]=v
    output['retry'] = {'null':'each full fixed-budget attempt has conditional expected difference zero',
        'analytic_expected_stopped_mean':.25,'analytic_expected_fixed_mean':0.,
        'mean_executed_attempts_per_task':float(used.mean()),'methods':rr,
        'warning':'fixed-denominator stopped sum is a different predeclared estimand; not general missing-value zero imputation'}
    cases=[]
    for ci,mu in enumerate([0.,.06,.2]):
        rng = np.random.default_rng(np.random.SeedSequence([seed,2,ci]))
        x = np.where(rng.random((reps,tasks)) < (1+mu)/2, 1.,-1.)
        missing = rng.random(x.shape) < np.where(x>0,.1,.5)
        # Fixed random audit is drawn independently of hidden outcomes, only missing units are audited.
        audit_u = rng.random(x.shape)
        methods={}
        for name,vals,inc in [('full_outcomes_reference',x,None),
                              ('complete_case_deletion',x,~missing),
                              ('missing_as_zero',np.where(missing,0.,x),None)]:
            p=process(vals,inc); methods[name]=summary(p)
            for k,v in p.items(): arrays[f'missing_{ci}_{name}_{k}']=v
        for audit_rate in [0.,.5,1.]:
            audited = missing & (audit_u < audit_rate)
            known = ~missing | audited
            lower = np.where(known,x,-1.)
            name=f'lower_bound_audit_{audit_rate:g}'
            p=process(lower);methods[name]=summary(p)
            methods[name]['mean_audited_tasks']=float(audited.sum(1).mean())
            methods[name]['analytic_lower_mean']=mu-(1+mu)*.1*(1-audit_rate)
            for k,v in p.items(): arrays[f'missing_{ci}_{name}_{k}']=v
        cases.append({'true_policy_mean':mu,'missing_rate_empirical':float(missing.mean()),
            'methods':methods,'analytic_complete_case_mean':(.9*(1+mu)-.5*(1-mu))/(.9*(1+mu)+.5*(1-mu)),
            'analytic_missing_zero_mean':.9*(1+mu)/2-.5*(1-mu)/2})
    output['missingness']=cases
    return output,arrays

def main() -> int:
    a=argparse.ArgumentParser();a.add_argument('--reps',type=int,default=3000);a.add_argument('--tasks',type=int,default=500)
    a.add_argument('--seed',type=int,default=SEED);a.add_argument('--output',type=Path,required=True)
    args=a.parse_args()
    if args.reps<2 or args.tasks<2: a.error('reps and tasks must be at least two')
    start=time.perf_counter();s,arr=analyze(args.reps,args.tasks,args.seed)
    data={'schema':'hermes.task-protocol-study.results.v1','config':{'reps':args.reps,'tasks':args.tasks,'seed':args.seed,'bets':BETS.tolist(),'alpha':ALPHA},
          'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),
            'threads':{k:os.getenv(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}},
          'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'wall_seconds_incidental':time.perf_counter()-start,'summary':s,'execution_authorized':False,
          'scope':'synthetic effect-level stress test, not live-Hermes validation'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2),encoding='utf-8')
    np.savez_compressed(args.output.with_suffix('.npz'),**arr)
    print(json.dumps(s,indent=2));return 0
if __name__=='__main__': raise SystemExit(main())
