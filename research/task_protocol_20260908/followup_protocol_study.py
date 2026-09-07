"""Fresh-seed follow-up: completion order and paired binary task outcomes."""
from __future__ import annotations
import hashlib,json,time
from pathlib import Path
import numpy as np
from run_protocol_study import process,summary

ROOT=Path(__file__).resolve().parents[1]
SEED=2026090851
REPS=3000
TASKS=500

def main():
    start=time.perf_counter();arrays={};rng=np.random.default_rng(SEED)
    x=np.where(rng.random((REPS,TASKS))<.5,1.,-1.)
    # Both signs finish eventually; negatives take longer on average.
    completion=rng.exponential(1.,x.shape)+np.where(x<0,3.,0.)
    permutation=np.argsort(completion,axis=1,kind='stable')
    arrived=np.take_along_axis(x,permutation,axis=1)
    canonical=process(x);arrival=process(arrived)
    terminal_equal=bool(np.array_equal(canonical['terminal'],arrival['terminal']))
    for name,result in [('enrollment_order',canonical),('completion_order',arrival)]:
        for k,v in result.items():arrays['order_'+name+'_'+k]=v
    # Effects are differences of genuine Bernoulli scores, not only +/-1 fixtures.
    rng=np.random.default_rng(SEED+1)
    ca=rng.random((REPS,TASKS,2))<.6
    ba=rng.random((REPS,TASKS,2))<.6
    delta=ca.astype(float)-ba.astype(float)
    used=np.where(delta[:,:,0]>0,1,2)
    protocols={'fixed_two_mean':delta.mean(2),
        'stopped_mean':np.where(used==1,delta[:,:,0],delta.mean(2))}
    ps={}
    for name,vals in protocols.items():
        p=process(vals);ps[name]=summary(p)
        for k,v in p.items():arrays['paired_'+name+'_'+k]=v
    out={'schema':'hermes.task-protocol-followup.results.v1',
         'seed':SEED,'reps':REPS,'tasks':TASKS,
         'completion_order':{'enrollment':summary(canonical),'arrival':summary(arrival),
              'terminal_decisions_identical':terminal_equal,
              'all_tasks_eventually_complete':True,'mean_completion_delay_negative_offset':3.},
         'paired_binary_scores':{'candidate_success':.6,'baseline_success':.6,
              'analytic_fixed_mean':0.,'analytic_stopped_mean':.12,
              'mean_attempts_executed':float(used.mean()),'methods':ps},
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'execution_authorized':False,'wall_seconds_incidental':time.perf_counter()-start}
    (ROOT/'results/followup.json').write_text(json.dumps(out,indent=2))
    np.savez_compressed(ROOT/'results/followup.npz',**arrays)
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
