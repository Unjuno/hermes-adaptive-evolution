from __future__ import annotations
import argparse, json, math, platform, sys
from pathlib import Path
import numpy as np

SEED = 2026090901

def ztest_rate_task_vs_episode(reps=5000, episodes=40, tasks_per_episode=10):
    rng=np.random.default_rng(SEED+1)
    task_reject=0; ep_reject=0
    task_z=[]; ep_z=[]
    for _ in range(reps):
        shock=rng.choice(np.array([-1.0,1.0]), size=episodes)
        # stateful memory/episode shock couples every task within an episode
        d=np.repeat(shock, tasks_per_episode)
        mt=d.mean(); st=d.std(ddof=1)/math.sqrt(len(d))
        zt=mt/max(st,1e-12)
        me=shock.mean(); se=shock.std(ddof=1)/math.sqrt(episodes)
        ze=me/max(se,1e-12)
        task_z.append(zt); ep_z.append(ze)
        task_reject += zt > 1.645
        ep_reject += ze > 1.645
    return {
        "reps":reps,"episodes":episodes,"tasks_per_episode":tasks_per_episode,
        "task_as_independent":{"false_positive_rate":task_reject/reps,"mean_z":float(np.mean(task_z))},
        "episode_as_independent":{"false_positive_rate":ep_reject/reps,"mean_z":float(np.mean(ep_z))},
    }

def warm_start_experiment(reps=2000, types=20, eval_tasks=200):
    rng=np.random.default_rng(SEED+2)
    rec=[]
    for _ in range(reps):
        truth=rng.integers(0,2,size=types)
        seq=rng.integers(0,types,size=eval_tasks)

        def run(initial_memory):
            mem=dict(initial_memory)
            success=0
            learned=0
            for typ in seq:
                if int(typ) in mem:
                    a=mem[int(typ)]
                else:
                    a=int(rng.integers(0,2))
                    learned += 1
                success += int(a==truth[typ])
                mem[int(typ)] = int(truth[typ])
            return success/eval_tasks, learned

        cold, learned=run({})
        endowed, _=run({i:int(truth[i]) for i in range(types)})
        matched, _=run({i:int(truth[i]) for i in range(types)})
        rec.append((cold,endowed,matched,learned))
    a=np.array(rec,float)
    return {
        "reps":reps,"types":types,"eval_tasks":eval_tasks,
        "cold_start_accuracy":float(a[:,0].mean()),
        "endowed_accuracy":float(a[:,1].mean()),
        "matched_endowment_accuracy":float(a[:,2].mean()),
        "endowed_minus_cold":float((a[:,1]-a[:,0]).mean()),
        "endowed_minus_matched":float((a[:,1]-a[:,2]).mean()),
        "mean_new_types_learned_by_cold":float(a[:,3].mean()),
        "interpretation":"Warm-start vs cold-start changes both policy code/state. Matching the initial memory removes the apparent algorithmic advantage."
    }

def order_experiment(reps=5000, n_each=100):
    rng=np.random.default_rng(SEED+3)
    def score(seq, capacity):
        # Wrong on first use of an uncached type, then stores it.
        cache=[]
        succ=0
        for typ in seq:
            if typ in cache:
                succ += 1
                cache.remove(typ); cache.append(typ)
            else:
                if len(cache)>=capacity: cache.pop(0)
                cache.append(typ)
        return succ/len(seq)
    block=np.array([0]*n_each+[1]*n_each)
    alternating=np.array([0,1]*n_each)
    rand_scores=[]
    for _ in range(reps):
        seq=np.array([0]*n_each+[1]*n_each)
        rng.shuffle(seq)
        rand_scores.append(score(seq,1))
    return {
        "same_multiset":{"type0":n_each,"type1":n_each},
        "capacity1":{
            "block_accuracy":score(block,1),
            "alternating_accuracy":score(alternating,1),
            "random_order_mean_accuracy":float(np.mean(rand_scores)),
            "random_order_sd":float(np.std(rand_scores,ddof=1)),
        },
        "capacity2":{
            "block_accuracy":score(block,2),
            "alternating_accuracy":score(alternating,2),
        },
        "interpretation":"A task multiset does not define the evaluation environment for stateful policies; sequence/order is part of the intervention."
    }

def poison_experiment(reps=5000, T=200, poison_at=40):
    rng=np.random.default_rng(SEED+4)
    periods=[5,10,20,50]
    out={"reps":reps,"T":T,"poison_at":poison_at,"poisoned":{},"clean":{}}
    # Randomize poison position within a small window so periodic phases are not hand-aligned.
    for condition in ("clean","poisoned"):
        records={f"periodic_{p}":[] for p in periods}
        records["sticky"]=[]
        records["verified_failure"]=[]
        for _ in range(reps):
            pt=poison_at+int(rng.integers(0,10)) if condition=="poisoned" else None

            # sticky memory: starts correct, ignores all later evidence
            mem=1; err=0
            for t in range(T):
                if pt is not None and t==pt: mem=0
                err += int(mem!=1)
            records["sticky"].append((err,0))

            # reliable verifier: one wrong action is detected, then memory corrected
            mem=1; err=0; probes=0
            for t in range(T):
                if pt is not None and t==pt: mem=0
                if mem!=1:
                    err += 1
                    probes += 1
                    mem=1
            records["verified_failure"].append((err,probes))

            for p in periods:
                mem=1;err=0;probes=0
                for t in range(T):
                    if pt is not None and t==pt: mem=0
                    if t % p == 0:
                        probes += 1
                        mem=1
                    err += int(mem!=1)
                records[f"periodic_{p}"].append((err,probes))
        for name,vals in records.items():
            a=np.array(vals,float)
            # cost: one wrong action =1 normalized loss; independent probe=.15 loss
            net=a[:,0]+.15*a[:,1]
            out[condition][name]={
                "mean_errors":float(a[:,0].mean()),
                "mean_probes":float(a[:,1].mean()),
                "mean_net_loss_error1_probe015":float(net.mean()),
            }
    out["interpretation"]="Memory freshness has value only relative to verification/probe cost. Blind persistence is optimal in clean stable worlds but catastrophic after a semantic poison."
    return out

def paired_episode_power(reps=4000, episodes=40, tasks_per_episode=10, mean_gain=.10):
    # Clustered episode gains: within-episode tasks share one stateful latent shock plus small iid noise.
    rng=np.random.default_rng(SEED+5)
    results={}
    for mu in [0.0,.03,.06,.10]:
        task_rej=0; ep_rej=0
        for _ in range(reps):
            shock=rng.normal(mu,1,size=episodes)
            d=shock[:,None] + rng.normal(0,.15,size=(episodes,tasks_per_episode))
            flat=d.ravel()
            zt=flat.mean()/(flat.std(ddof=1)/math.sqrt(flat.size))
            epm=d.mean(axis=1)
            ze=epm.mean()/(epm.std(ddof=1)/math.sqrt(episodes))
            task_rej += zt>1.645
            ep_rej += ze>1.645
        results[str(mu)]={
            "task_as_independent_rate":task_rej/reps,
            "episode_aggregate_rate":ep_rej/reps,
        }
    return {"reps":reps,"episodes":episodes,"tasks_per_episode":tasks_per_episode,"rates":results}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result={
        "schema":"hermes.r1-stateful-memory-evaluation.v0.1",
        "seed":SEED,
        "environment":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()},
        "warm_start":warm_start_experiment(),
        "cluster_null":ztest_rate_task_vs_episode(),
        "cluster_power":paired_episode_power(),
        "sequence_order":order_experiment(),
        "memory_poison":poison_experiment(),
        "authority":"offline_research_only",
        "execution_authorized":False,
    }
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({
      "warm_start":result["warm_start"],
      "cluster_null":result["cluster_null"],
      "cluster_power":result["cluster_power"],
      "sequence_order":result["sequence_order"],
      "memory_poison":result["memory_poison"],
    },indent=2))
if __name__=="__main__":
    main()
