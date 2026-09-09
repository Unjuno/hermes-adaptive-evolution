from __future__ import annotations
import argparse,json,sys,platform
from pathlib import Path
import numpy as np
SEED=2026090903

def run(reps=5000,T=300,hazard=.002,probe_cost=.15):
    rng=np.random.default_rng(SEED)
    periodic=(5,10,20,50)
    sensitivities=(1.0,.5,.2,.1,.05)
    false_alarms=(0.0,.001,.005)
    out={}
    for fpr in false_alarms:
        out[str(fpr)]={}
        for sens in sensitivities:
            losses={f"periodic_{p}":[] for p in periodic}
            losses["event_verifier"]=[]
            for _ in range(reps):
                poisons=rng.random(T)<hazard
                # event-driven verifier: wrong action yields a detect signal with sensitivity;
                # correct action can trigger false alarm with probability fpr.
                mem=1;err=0;probes=0
                for t in range(T):
                    if poisons[t]:mem=0
                    wrong=mem!=1
                    if wrong:err+=1
                    detect=(wrong and rng.random()<sens) or ((not wrong) and rng.random()<fpr)
                    if detect:
                        probes+=1;mem=1
                losses["event_verifier"].append(err+probe_cost*probes)
                for p in periodic:
                    mem=1;err=0;probes=0;phase=int(rng.integers(0,p))
                    for t in range(T):
                        if poisons[t]:mem=0
                        if (t-phase)%p==0:
                            probes+=1;mem=1
                        err+=mem!=1
                    losses[f"periodic_{p}"].append(err+probe_cost*probes)
            means={k:float(np.mean(v)) for k,v in losses.items()}
            out[str(fpr)][str(sens)]={"mean_net_loss":means,"best_method":min(means,key=means.get)}
    return {
      "schema":"hermes.r1-memory-verifier-frontier.v0.1","seed":SEED,
      "config":{"reps":reps,"T":T,"poison_hazard":hazard,"probe_cost":probe_cost},
      "frontier":out,
      "environment":{"python":sys.version,"numpy":np.__version__,"platform":platform.platform()},
      "interpretation":"Event-triggered freshness dominates only when failure evidence is sufficiently reliable/cheap; otherwise scheduled probes can have lower net loss.",
      "authority":"offline_research_only","execution_authorized":False
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,required=True);a=ap.parse_args()
    out=run();a.output.write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out["frontier"],indent=2))
if __name__=="__main__":main()
