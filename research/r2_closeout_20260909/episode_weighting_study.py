"""Prespecified episode-vs-task weighting diagnostic; no model/provider calls."""
from __future__ import annotations
import argparse,hashlib,json,math,platform,sys
from pathlib import Path
import numpy as np
SEED=2026090931
BETS=np.array([0.,.02,.05,.1,.2,.4,.8])
def crossings(x):
    logs=np.zeros((len(x),len(BETS)));hit=np.zeros(len(x),bool)
    for i in range(x.shape[1]):
        logs+=np.log1p(x[:,i,None]*BETS)
        high=logs.max(1)
        log_e=high+np.log(np.exp(logs-high[:,None]).mean(1))
        hit|=log_e>=math.log(20)
    return hit
def rate(x):
    n=len(x);k=int(x.sum());p=k/n;z=1.959963984540054
    den=1+z*z/n;c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {"count":k,"n":n,"rate":p,"wilson95":[c-h,c+h]}
def main():
    a=argparse.ArgumentParser();a.add_argument("--output",type=Path,required=True)
    a.add_argument("--seed",type=int,default=SEED);args=a.parse_args()
    rows=[]
    for ci,condition in enumerate(("length_independent","positive_long","negative_long")):
        rng=np.random.default_rng(np.random.SeedSequence([args.seed,ci]))
        d=rng.choice(np.array([-.8,.8]),size=(4000,120))
        if condition=="length_independent":n=rng.choice([1,9],size=d.shape)
        else:n=np.where(d>0,9 if condition=="positive_long" else 1,1 if condition=="positive_long" else 9)
        # Each column is one independent episode in BOTH methods.
        # The second method changes weights/estimand, not the count of units.
        weighted=d*n/9
        theory_task={"length_independent":0.,"positive_long":.64,"negative_long":-.64}[condition]
        rows.append({"condition":condition,"units_per_world":120,
           "known_equal_episode_mean":0.,"known_long_run_equal_task_mean":theory_task,
           "episode_objective_crossings":rate(crossings(d)),
           "task_objective_crossings":rate(crossings(weighted)),
           "empirical_episode_mean":float(d.mean()),
           "empirical_task_mean":float((n*d).sum()/n.sum()),
           "warning":"Task-target positive results are valid for that different estimand; not universal false positives."})
    result={"schema":"hermes.episode-weighting-study.v1","seed":args.seed,
       "plan":"FOLLOWUP_PLAN.json (metric comparison elaboration in source, no tuned thresholds)",
       "rows":rows,"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       "environment":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()},
       "execution_authorized":False,"scope":"offline synthetic"}
    if args.output.exists():raise ValueError("refuse overwrite")
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(rows,indent=2))
if __name__=="__main__":main()
