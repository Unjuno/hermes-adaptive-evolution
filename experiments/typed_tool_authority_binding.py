from __future__ import annotations
import argparse,json,math
import numpy as np
from typing import List

POLICIES=('actor_field_gate','registry_stale','registry_failclosed','registry_degraded')
V1=frozenset({0,1});V2=frozenset({0,1,2,3});COARSE=frozenset({0,1,2,3,4})

def root_available(t,shift=180,outage=60):return not (shift<=t<shift+outage)
def true_reg(t,shift=180):return V2 if t>=shift else V1

def run(seed,policy,steps=360,manip_p=.25,shift=180,outage=60):
    r=np.random.default_rng(610000+seed);cached=V1;ver=1;protected_ver=1;mode='NORMAL';last=-999
    us=[];leaks=[];falseb=[];blocks=[];roots=[];deg=[];fc=[];lies=[]
    for t in range(steps):
        true=true_reg(t,shift);truev=2 if t>=shift else 1
        if truev>protected_ver:protected_ver=truev
        tool='delete' if r.random()<.4 else 'write'
        attack=bool(r.random()<manip_p)
        if attack:
            key=int(r.choice(sorted(true)))
        else:
            safe=[k for k in range(12) if k not in true];key=int(r.choice(safe))
        actor_protected=False if attack else (key in V1)  # attacker lies; benign actor has stale v1 view
        value=float(r.uniform(.8,1.2));root=False
        if policy.startswith('registry_') and ver!=protected_ver:
            if policy=='registry_stale':mode='STALE'
            elif t-last>=8 or root_available(t,shift,outage):
                last=t;root=True
                if root_available(t,shift,outage):cached=true;ver=truev;mode='NORMAL'
                else:mode='DEGRADED' if policy=='registry_degraded' else 'FAIL_CLOSED'
            else:mode='DEGRADED' if policy=='registry_degraded' else 'FAIL_CLOSED'
        if policy=='actor_field_gate':allowed=not actor_protected
        elif policy=='registry_stale':allowed=key not in cached
        elif policy=='registry_failclosed':allowed=False if mode=='FAIL_CLOSED' else (key not in cached)
        elif policy=='registry_degraded':allowed=key not in (COARSE if mode=='DEGRADED' else cached)
        else:raise ValueError(policy)
        true_safe=key not in true
        if allowed:
            leak=not true_safe;u=value if true_safe else -value
        else:
            leak=False;u=.55*value  # safe read/inspect fallback
        us.append(u-(.005 if root else 0));leaks.append(leak);blocks.append(not allowed);falseb.append((not allowed) and true_safe);roots.append(root);deg.append(mode=='DEGRADED');fc.append(mode=='FAIL_CLOSED');lies.append(attack and not actor_protected)
    return {'seed':seed,'policy':policy,'mean_utility':float(np.mean(us)),'uncertified_leak_rate':float(np.mean(leaks)),'any_invariant_violation':bool(np.any(leaks)),'false_block_rate':float(np.mean(falseb)),'block_rate':float(np.mean(blocks)),'root_call_rate':float(np.mean(roots)),'degraded_rate':float(np.mean(deg)),'failclosed_rate':float(np.mean(fc)),'lying_metadata_rate':float(np.mean(lies))}

def ci(v:List[float]):
    x=np.asarray(v,float);m=float(x.mean());se=float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else 0;return [m,m-1.96*se,m+1.96*se]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=64);ap.add_argument('--out',required=True);ap.add_argument('--manip-p',type=float,default=.25);ap.add_argument('--shift',type=int,default=180);ap.add_argument('--outage',type=int,default=60);a=ap.parse_args();base=370000+int(a.manip_p*1000);rows=[]
    for i in range(a.seeds):
        for p in POLICIES:rows.append(run(base+i,p,manip_p=a.manip_p,shift=a.shift,outage=a.outage))
    metrics=['mean_utility','uncertified_leak_rate','any_invariant_violation','false_block_rate','block_rate','root_call_rate','degraded_rate','failclosed_rate','lying_metadata_rate']
    s={p:{k:float(np.mean([float(r[k]) for r in rows if r['policy']==p])) for k in metrics} for p in POLICIES};s['paired']={}
    for q in ('actor_field_gate','registry_stale','registry_failclosed'):
        ds={k:[] for k in ('mean_utility','uncertified_leak_rate','any_invariant_violation','false_block_rate')}
        for i in range(a.seeds):
            seed=base+i;x=next(r for r in rows if r['seed']==seed and r['policy']=='registry_degraded');y=next(r for r in rows if r['seed']==seed and r['policy']==q)
            for k in ds:ds[k].append(float(x[k])-float(y[k]))
        s['paired']['registry_degraded-vs-'+q]={k:ci(v) for k,v in ds.items()}
    out={'schema':'adaptive-evolution.typed-tool-authority-binding.v0.1','seeds':a.seeds,'manip_p':a.manip_p,'shift':a.shift,'outage':a.outage,'summary':s,'rows':rows}
    open(a.out,'w').write(json.dumps(out,indent=2));print(json.dumps(s,indent=2))
if __name__=='__main__':main()
