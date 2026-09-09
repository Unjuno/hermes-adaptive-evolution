from __future__ import annotations
import argparse,json,sys,platform
from pathlib import Path
import numpy as np
SEED=2026090905

def simulate(reps=1000,agents=4,types=20,train_steps=400,eval_steps=600,
             acquisition_query_cost=.05,fallback_query_cost=.20):
    rng=np.random.default_rng(SEED)
    poison_probs=(0.0,.01,.05,.10,.25,.50,1.0)
    quorums=(1,2,3,4)
    out={}
    for pp in poison_probs:
        rec={q:[] for q in quorums}
        for _ in range(reps):
            truth=rng.integers(0,2,size=types)
            ta=rng.integers(0,agents,size=train_steps)
            tt=rng.integers(0,types,size=train_steps)
            poison = rng.random()<pp
            poison_type=int(rng.integers(0,types))
            poison_agent=int(rng.integers(0,agents))
            ea=rng.integers(0,agents,size=eval_steps)
            et=rng.integers(0,types,size=eval_steps)
            for q in quorums:
                mem={t:{} for t in range(types)}
                queries=0
                for a,t in zip(ta,tt):
                    a=int(a);t=int(t)
                    if len(mem[t])>=q: continue
                    if a not in mem[t]:
                        queries+=1
                        mem[t][a]=int(truth[t])
                if poison:
                    vals=mem[poison_type]
                    if vals:
                        target=poison_agent if poison_agent in vals else next(iter(vals))
                        vals[target]=1-vals[target]
                errors=0;fallbacks=0
                for a,t in zip(ea,et):
                    t=int(t); vals=mem[t]
                    c0=sum(v==0 for v in vals.values()); c1=sum(v==1 for v in vals.values())
                    if len(vals)>=q and c0!=c1:
                        pred=1 if c1>c0 else 0
                        errors += pred!=truth[t]
                    else:
                        fallbacks+=1
                net=errors + acquisition_query_cost*queries + fallback_query_cost*fallbacks
                rec[q].append((net,queries,errors,fallbacks))
        out[str(pp)]={}
        for q in quorums:
            a=np.array(rec[q],float)
            out[str(pp)][str(q)]={
              "mean_net_loss":float(a[:,0].mean()),
              "mean_acquisition_queries":float(a[:,1].mean()),
              "mean_poison_errors":float(a[:,2].mean()),
              "mean_fallback_queries":float(a[:,3].mean()),
            }
        best=min(quorums,key=lambda q:out[str(pp)][str(q)]["mean_net_loss"])
        out[str(pp)]["best_quorum"]=best
    return {
      "schema":"hermes.r1-organizational-memory-quorum-fcv.v0.1","seed":SEED,
      "config":{"reps":reps,"agents":agents,"types":types,"train_steps":train_steps,
                "eval_steps":eval_steps,"acquisition_query_cost":acquisition_query_cost,
                "fallback_query_cost":fallback_query_cost},
      "poison_probability_frontier":out,
      "environment":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()},
      "interpretation":"Memory replication/quorum is an FCV coordinate balancing acquisition delay, fallback cost, and common-cause poison exposure.",
      "authority":"offline_research_only","execution_authorized":False
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    out=simulate();a.output.write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out["poison_probability_frontier"],indent=2))
if __name__=="__main__":main()
