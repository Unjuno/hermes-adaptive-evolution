from __future__ import annotations
import argparse,json,math
from dataclasses import dataclass,asdict
from typing import List
import numpy as np
import typed_tool_transfer as tt

POLICIES=("single_hold","dual_hold","independent_cut","delayed_cut","cut_10pct_failure")

@dataclass(frozen=True)
class Cfg:
    hold_independent_fail_p:float=.12
    hold_common_fail_p:float=.03
    cut_fail_p:float=.10
    cut_latency:int=2


def add_interlock_faults(seed:int,steps:int):
    r=np.random.default_rng(420000+seed)
    return {
      'hold_common_u':r.random(steps),
      'hold_fail_u':r.random((steps,2)),
      'cut_fail_u':r.random(steps),
    }


def hold_success(F,t,cfg,channels):
    if F['hold_common_u'][t] < cfg.hold_common_fail_p:return False
    return not bool(np.all(F['hold_fail_u'][t,:channels] < cfg.hold_independent_fail_p))


def run(seed:int,sc:tt.Scenario,policy:str,cfg=Cfg(),steps:int=360):
    rng=np.random.default_rng(50000+seed)
    faults=tt.build_faults(np.random.default_rng(90000+seed),steps,sc)
    I=add_interlock_faults(seed,steps)
    balances=np.full(4,.55,float);cached=tt.META_V1;protected_version=1;mode='NORMAL';last_refresh=-999;root_calls=0
    suspend=np.zeros(4,dtype=int)  # tool-domain suspension countdown after delayed cut
    us=[];leaks=[];blocks=[];fbfails=[];holdattempt=[];holdfails=[];cuts=[];cutfails=[];suspsteps=[]
    for t in range(steps):
        tm=tt.true_meta(t,sc)
        if tm.version>protected_version:protected_version=tm.version
        call=tt.generate_selected_call(rng,t,sc,balances)
        d=tt.tool_domain(call.tool)
        cost=0.0
        if cached.version!=protected_version:
            if t-last_refresh>=8 or tt.root_available(t,sc):
                last_refresh=t;root_calls+=1;cost+=.006
                if tt.root_available(t,sc):cached=tm;mode='NORMAL'
                else:mode='DEGRADED'
            else:mode='DEGRADED'
        gate=tt.COARSE if mode=='DEGRADED' else cached
        blocked=not tt.certified(call,gate,balances)
        selected=call;fbfail=False;ha=False;hf=False;cut=False;cf=False
        # already cut/suspended tool domain cannot execute mutating operations; read remains allowed.
        if suspend[d]>0 and call.tool!='read':
            suspend[d]-=1; selected=None
        elif blocked:
            fb=tt.safe_fallback(call,gate,balances)
            if fb is not None and tt.certified(fb,gate,balances):
                pd=tt.tool_domain(call.tool);fd=tt.tool_domain(fb.tool)
                ok=(not faults['domain_down'][t,fd]) and not (fd==pd and faults['common_u'][t]<sc.fallback_common_p) and faults['fallback_u'][t]>=sc.fallback_independent_fail_p
            else: ok=False
            if ok:
                selected=fb
            else:
                fbfail=True;ha=True
                channels=1 if policy=='single_hold' else 2
                hs=hold_success(I,t,cfg,channels)
                if hs:selected=None
                else:
                    hf=True
                    if policy in ('single_hold','dual_hold'):
                        selected=call  # fail-open after terminal hold failure
                    elif policy=='independent_cut':
                        cut=True;selected=None
                    elif policy=='delayed_cut':
                        cut=True;selected=call;suspend[d]=cfg.cut_latency
                    elif policy=='cut_10pct_failure':
                        cut=True;cf=bool(I['cut_fail_u'][t] < cfg.cut_fail_p);selected=call if cf else None
                    else:raise ValueError(policy)
        emode='fallback' if (selected is not None and selected is not call) else ('hold' if selected is None else 'primary')
        u,success,leak=tt.execute(selected,tm,balances,emode);u-=cost
        us.append(u);leaks.append(leak);blocks.append(blocked);fbfails.append(fbfail);holdattempt.append(ha);holdfails.append(hf);cuts.append(cut);cutfails.append(cf);suspsteps.append(bool(np.any(suspend>0)))
    return {'seed':seed,'policy':policy,'mean_utility':float(np.mean(us)),'uncertified_leak_rate':float(np.mean(leaks)),'any_invariant_violation':bool(np.any(leaks)),'hard_block_rate':float(np.mean(blocks)),'fallback_failure_rate':float(np.mean(fbfails)),'hold_attempt_rate':float(np.mean(holdattempt)),'hold_failure_rate':float(np.mean(holdfails)),'capability_cut_rate':float(np.mean(cuts)),'cut_failure_rate':float(np.mean(cutfails)),'suspended_rate':float(np.mean(suspsteps)),'root_call_rate':root_calls/steps}


def ci(v:List[float]):
    x=np.asarray(v,float);m=float(x.mean());se=float(x.std(ddof=1)/math.sqrt(len(x))) if len(x)>1 else 0;return [m,m-1.96*se,m+1.96*se]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=64);ap.add_argument('--scenario',default='combined');ap.add_argument('--out',required=True);a=ap.parse_args()
    sc=next(s for s in tt.SCENARIOS if s.name==a.scenario);cfg=Cfg();base=310000;rows=[]
    for i in range(a.seeds):
        for p in POLICIES:rows.append(run(base+i,sc,p,cfg))
    metrics=['mean_utility','uncertified_leak_rate','any_invariant_violation','hard_block_rate','fallback_failure_rate','hold_failure_rate','capability_cut_rate','cut_failure_rate','suspended_rate']
    summary={p:{k:float(np.mean([float(r[k]) for r in rows if r['policy']==p])) for k in metrics} for p in POLICIES}
    summary['paired']={}
    for p in ('single_hold','dual_hold','delayed_cut','cut_10pct_failure'):
        ds={k:[] for k in ('mean_utility','uncertified_leak_rate','any_invariant_violation')}
        for i in range(a.seeds):
            seed=base+i;x=next(r for r in rows if r['seed']==seed and r['policy']=='independent_cut');y=next(r for r in rows if r['seed']==seed and r['policy']==p)
            for k in ds:ds[k].append(float(x[k])-float(y[k]))
        summary['paired']['independent_cut-vs-'+p]={k:ci(v) for k,v in ds.items()}
    out={'schema':'adaptive-evolution.typed-tool-tcb-faults.v0.1','seeds':a.seeds,'scenario':asdict(sc),'config':asdict(cfg),'summary':summary,'rows':rows}
    with open(a.out,'w') as f:json.dump(out,f,indent=2)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
