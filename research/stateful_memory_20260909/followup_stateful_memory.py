from __future__ import annotations
import argparse,json,math,sys,platform
from pathlib import Path
import numpy as np
SEED=2026090902

def cluster_grid(reps=5000,episodes=40):
    rng=np.random.default_rng(SEED+1)
    out={}
    for m in (1,2,5,10,20):
        out[str(m)]={}
        for rho in (0.0,.25,.5,.9):
            task=0;ep=0
            for _ in range(reps):
                shock=rng.normal(size=(episodes,1))
                eps=rng.normal(size=(episodes,m))
                d=np.sqrt(rho)*shock+np.sqrt(1-rho)*eps
                flat=d.ravel()
                zt=flat.mean()/(flat.std(ddof=1)/math.sqrt(flat.size))
                em=d.mean(1)
                ze=em.mean()/(em.std(ddof=1)/math.sqrt(episodes))
                task += zt>1.645
                ep += ze>1.645
            out[str(m)][str(rho)]={
              "task_naive_fpr":task/reps,
              "episode_aggregate_fpr":ep/reps,
              "nominal_task_count":episodes*m,
              "independent_episode_count":episodes,
              "design_effect_theory":1+(m-1)*rho,
              "effective_task_count_approx":episodes*m/(1+(m-1)*rho),
            }
    return out

def memory_hazard(reps=5000,T=300):
    rng=np.random.default_rng(SEED+2)
    periods=(5,10,20,50,100)
    hazards=(0.0,.0005,.001,.002,.005,.01)
    probe_cost=.15
    out={}
    for h in hazards:
        methods={f"periodic_{p}":[] for p in periods}
        methods["sticky"]=[];methods["verified_failure"]=[]
        for _ in range(reps):
            poisons=rng.random(T)<h
            mem=1;err=0;probes=0
            for t in range(T):
                if poisons[t]: mem=0
                err+=mem!=1
            methods["sticky"].append(err+probe_cost*probes)
            mem=1;err=0;probes=0
            for t in range(T):
                if poisons[t]: mem=0
                if mem!=1:
                    err+=1;probes+=1;mem=1
            methods["verified_failure"].append(err+probe_cost*probes)
            for p in periods:
                mem=1;err=0;probes=0
                phase=int(rng.integers(0,p))
                for t in range(T):
                    if poisons[t]: mem=0
                    if (t-phase)%p==0:
                        probes+=1;mem=1
                    err+=mem!=1
                methods[f"periodic_{p}"].append(err+probe_cost*probes)
        means={k:float(np.mean(v)) for k,v in methods.items()}
        best=min(means,key=means.get)
        out[str(h)]={"mean_net_loss":means,"best_method":best}
    return {"T":T,"reps":reps,"probe_cost":probe_cost,"hazards":out}

def acquisition_cost(reps=3000,types=20,eval_tasks=200):
    rng=np.random.default_rng(SEED+3)
    costs=(0,.1,.25,.5,1.0)
    rec={str(c):[] for c in costs}
    raw=[]
    for _ in range(reps):
        truth=rng.integers(0,2,size=types);seq=rng.integers(0,types,size=eval_tasks)
        mem={};errors=0
        for typ in seq:
            typ=int(typ)
            if typ in mem:a=mem[typ]
            else:a=int(rng.integers(0,2))
            errors+=a!=truth[typ];mem[typ]=int(truth[typ])
        cold_loss=errors
        for c in costs:
            endowed_loss=c*types
            rec[str(c)].append(endowed_loss-cold_loss)
        raw.append(errors)
    return {
      "mean_cold_first-encounter_errors":float(np.mean(raw)),
      "endowed_minus_cold_net_loss":{k:float(np.mean(v)) for k,v in rec.items()},
      "break_even_cost_per_memory_entry_approx":float(np.mean(raw)/types),
      "interpretation":"If memory acquisition is part of the policy lifecycle, it must be charged. If memory is an exogenous fixed endowment, do not charge it but compare matched endowments."
    }

def burstiness(reps=5000,T=400):
    rng=np.random.default_rng(SEED+4)
    out={}
    for stay in (.5,.7,.9,.97,.99):
        vals=[]
        for _ in range(reps):
            seq=np.empty(T,int);seq[0]=int(rng.integers(0,2))
            for t in range(1,T):
                seq[t]=seq[t-1] if rng.random()<stay else 1-seq[t-1]
            cache=None;succ=0
            for typ in seq:
                if cache==typ:succ+=1
                cache=int(typ)
            vals.append(succ/T)
        out[str(stay)]={"capacity1_accuracy":float(np.mean(vals)),"sd":float(np.std(vals,ddof=1))}
    return {
      "T":T,"reps":reps,"stationary_type_fraction":"approximately 0.5/0.5 for all conditions",
      "results":out,
      "interpretation":"Task transition structure, not only the marginal task distribution, determines stateful-policy value."
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    out={"schema":"hermes.r1-stateful-memory-followup.v0.1","seed":SEED,
         "environment":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()},
         "cluster_grid":cluster_grid(),"memory_hazard":memory_hazard(),
         "memory_acquisition_cost":acquisition_cost(),"task_burstiness":burstiness(),
         "authority":"offline_research_only","execution_authorized":False}
    a.output.write_text(json.dumps(out,indent=2),encoding="utf-8")
    print(json.dumps({
      "cluster_grid":out["cluster_grid"],
      "memory_hazard":out["memory_hazard"],
      "memory_acquisition_cost":out["memory_acquisition_cost"],
      "task_burstiness":out["task_burstiness"]
    },indent=2))
if __name__=="__main__":main()
