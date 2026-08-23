from __future__ import annotations
import argparse,json,math
import numpy as np
from typing import List

POLICIES=('check_then_use','recheck_before_commit','reservation_token')

def run(seed,policy,steps=600,race_p=.18,reservation_cost=.002):
    r=np.random.default_rng(730000+seed);balances=np.full(4,.50,float)
    us=[];leaks=[];aborts=[];success=[];races=[]
    for t in range(steps):
        src=int(r.integers(0,4));dst=(src+int(r.integers(1,4)))%4
        # Proposed amount is certified at validation time under a 0.12 per-call cap.
        maxamt=min(.12,max(.015,balances[src]*.65));amt=float(r.uniform(.01,maxamt))
        validated=(amt<=.12 and amt<=balances[src])
        assert validated
        reserved=0.0
        if policy=='reservation_token':
            # Atomic validation+reservation: concurrent actors can only consume unreserved balance.
            balances[src]-=amt;reserved=amt
        race=bool(r.random()<race_p);races.append(race)
        if race:
            available=max(0.0,balances[src])
            drain=float(r.uniform(.02,min(.16,max(.021,available)))) if available>.02 else available
            balances[src]-=drain
        if policy=='check_then_use':
            safe_now=amt<=balances[src]+1e-12
            balances[src]-=amt;balances[dst]+=amt
            leak=not safe_now
            if leak:
                u=-.8;balances[src]=max(0.0,balances[src])
            else:u=1.0
            abort=False;ok=not leak
        elif policy=='recheck_before_commit':
            safe_now=amt<=balances[src]+1e-12
            if safe_now:
                balances[src]-=amt;balances[dst]+=amt;u=1.0;abort=False;ok=True;leak=False
            else:
                u=.18;abort=True;ok=False;leak=False
        elif policy=='reservation_token':
            # Amount was removed from spendable balance before the race; commit only transfers reserved units.
            balances[dst]+=reserved;u=1.0-reservation_cost;abort=False;ok=True;leak=False
        else:raise ValueError(policy)
        # External replenishment models new income/resources and prevents terminal depletion.
        balances=np.minimum(.65,balances+.018)
        us.append(u);leaks.append(leak);aborts.append(abort);success.append(ok)
    return {'seed':seed,'policy':policy,'mean_utility':float(np.mean(us)),'uncertified_commit_rate':float(np.mean(leaks)),'any_invariant_violation':bool(np.any(leaks)),'abort_rate':float(np.mean(aborts)),'task_success_rate':float(np.mean(success)),'race_rate':float(np.mean(races))}

def ci(v:List[float]):
    x=np.asarray(v,float);m=float(x.mean());se=float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else 0;return [m,m-1.96*se,m+1.96*se]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=64);ap.add_argument('--race-p',type=float,default=.18);ap.add_argument('--reservation-cost',type=float,default=.002);ap.add_argument('--out',required=True);a=ap.parse_args();base=440000+int(a.race_p*1000);rows=[]
    for i in range(a.seeds):
        for p in POLICIES:rows.append(run(base+i,p,race_p=a.race_p,reservation_cost=a.reservation_cost))
    metrics=['mean_utility','uncertified_commit_rate','any_invariant_violation','abort_rate','task_success_rate','race_rate']
    s={p:{k:float(np.mean([float(r[k]) for r in rows if r['policy']==p])) for k in metrics} for p in POLICIES};s['paired']={}
    for q in ('check_then_use','recheck_before_commit'):
        ds={k:[] for k in ('mean_utility','uncertified_commit_rate','any_invariant_violation','abort_rate','task_success_rate')}
        for i in range(a.seeds):
            seed=base+i;x=next(r for r in rows if r['seed']==seed and r['policy']=='reservation_token');y=next(r for r in rows if r['seed']==seed and r['policy']==q)
            for k in ds:ds[k].append(float(x[k])-float(y[k]))
        s['paired']['reservation_token-vs-'+q]={k:ci(v) for k,v in ds.items()}
    out={'schema':'adaptive-evolution.typed-tool-toctou.v0.1','seeds':a.seeds,'race_p':a.race_p,'reservation_cost':a.reservation_cost,'summary':s,'rows':rows};open(a.out,'w').write(json.dumps(out,indent=2));print(json.dumps(s,indent=2))
if __name__=='__main__':main()
