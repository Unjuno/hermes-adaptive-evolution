from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
SEED=2026091104;T=80;ALPHA=.01;CAL=10000;EVAL=5000;MU=1.0;SW=.25
HAZ=(.01,.02,.05,.1,.15,.25)

def states(r,R,h):
    z=r.random(R)<.5;o=np.empty((R,T),bool);o[:,0]=z
    for t in range(1,T):
        u=r.random(R);z=np.where(z,~(u<h),u<h);o[:,t]=z
    return o

def llr(r,z):
    x=r.normal(np.where(z,MU,0.),1.);return MU*x-.5*MU*MU

def fixed2(L,h):
    R,_=L.shape;a=np.zeros(R,bool);c=np.zeros(R,np.int16);A=np.empty_like(L,bool);sw=np.zeros(R,np.int16)
    for t in range(T):
        q=np.where(a,L[:,t]<-h,L[:,t]>h);c=np.where(q,c+1,0);f=c>=2
        a=np.where(f,~a,a);sw+=f;c=np.where(f,0,c);A[:,t]=a
    return A,sw

def cusum(L,h):
    R,_=L.shape;a=np.zeros(R,bool);s=np.zeros(R);A=np.empty_like(L,bool);sw=np.zeros(R,np.int16)
    for t in range(T):
        s=np.maximum(0,s+np.where(a,-L[:,t],L[:,t]));f=s>=h
        a=np.where(f,~a,a);sw+=f;s=np.where(f,0,s);A[:,t]=a
    return A,sw

def hmm(L,h,pth):
    R,_=L.shape;p=np.full(R,.5);a=np.zeros(R,bool);A=np.empty_like(L,bool);sw=np.zeros(R,np.int16)
    for t in range(T):
        q=np.clip(p*(1-h)+(1-p)*h,1e-12,1-1e-12)
        lo=np.log(q)-np.log1p(-q)+L[:,t];p=1/(1+np.exp(-np.clip(lo,-60,60)))
        f=np.where(a,p<1-pth,p>pth);a=np.where(f,~a,a);sw+=f;A[:,t]=a
    return A,sw

def cal_generic(kind):
    r=np.random.default_rng(SEED+11);L=llr(r,np.zeros((CAL,T),bool));lo,hi=0.,20.
    for _ in range(24):
        x=(lo+hi)/2;A,_=(fixed2(L,x) if kind=='fixed2' else cusum(L,x))
        if np.mean(A.any(1))>ALPHA:lo=x
        else:hi=x
    return hi

def cal_hmm(h):
    r=np.random.default_rng(SEED+int(h*100000));L=llr(r,np.zeros((CAL,T),bool));lo,hi=.5,.9999999
    for _ in range(24):
        x=(lo+hi)/2;A,_=hmm(L,h,x)
        if np.mean(A.any(1))>ALPHA:lo=x
        else:hi=x
    return hi

def loss(z,A,sw):return float(np.mean((z!=A).sum(1)+SW*sw))

def run():
    fh=cal_generic('fixed2');ch=cal_generic('cusum');hp={h:cal_hmm(h) for h in HAZ}
    methods=['fixed2','cusum']+[f'hmm_assumed_{h}' for h in HAZ];rows={}
    for trueh in HAZ:
        r=np.random.default_rng(SEED+9000+int(trueh*100000));z=states(r,EVAL,trueh);L=llr(r,z);vals={}
        A,s=fixed2(L,fh);vals['fixed2']=loss(z,A,s)
        A,s=cusum(L,ch);vals['cusum']=loss(z,A,s)
        for h in HAZ:
            A,s=hmm(L,h,hp[h]);vals[f'hmm_assumed_{h}']=loss(z,A,s)
        rows[str(trueh)]=vals
    oracle={h:min(v.values()) for h,v in rows.items()};rob={}
    for m in methods:
        arr=[rows[str(h)][m] for h in HAZ];reg=[rows[str(h)][m]-oracle[str(h)] for h in HAZ]
        rob[m]={'mean_loss':float(np.mean(arr)),'worst_loss':float(np.max(arr)),'mean_regret_to_best':float(np.mean(reg)),'worst_regret_to_best':float(np.max(reg))}
    return {'schema':'hermes.r3-hazard-robustness.v0.1','seed':SEED,'mu':MU,'switch_cost':SW,'hazards':HAZ,'thresholds':{'fixed2':fh,'cusum':ch,'hmm':hp},'loss_by_true_hazard':rows,'robustness':rob,'rank_mean_regret':sorted(rob,key=lambda m:rob[m]['mean_regret_to_best']),'authority':'offline_research_only','execution_authorized':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise ValueError('refuse existing output')
    out=run();a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
