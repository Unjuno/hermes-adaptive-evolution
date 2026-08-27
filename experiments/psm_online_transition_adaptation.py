from __future__ import annotations
import json
import numpy as np

SEED=20260828
rng=np.random.default_rng(SEED)
C,W=3,6
EP,T,DRIFT=5000,700,300

Q_PRE=np.array([[.96,.03,.01],[.04,.92,.04],[.02,.08,.90]],float)
Q_POST=np.array([[.80,.13,.07],[.05,.77,.18],[.01,.04,.95]],float)
E=np.array([[.62,.28,.10],[.25,.55,.20],[.12,.28,.60]],float)

BASE=np.array([
 [.05,.60,.15,.10,.05,.05],
 [.05,.10,.35,.25,.20,.05],
 [.05,.10,.15,.25,.35,.10],
 [.05,.10,.20,.10,.45,.10],
 [.05,.10,.10,.05,.60,.10],
 [.20,.25,.20,.10,.10,.15]],float)

def norm(M):
    M=np.maximum(M,1e-15)
    return M/M.sum(axis=-1,keepdims=True)

def wfkernel(c):
    M=BASE.copy()
    if c==0: M[:,4]*=1.65; M[:,3]*=.60; M[:,5]*=.65
    elif c==1: M[:,1]*=1.30; M[:,2]*=1.45; M[:,3]*=1.65; M[:,4]*=.60
    else: M[:,2]*=1.85; M[:,3]*=1.30; M[:,4]*=.30; M[:,5]*=1.90
    return norm(.988*norm(M)+.012*np.ones_like(M)/W)
PCTX=np.stack([wfkernel(c) for c in range(C)])

R=np.array([[.45,.65,.68,.58,1,.42],[.40,.83,.90,1,.58,.55],[.32,.64,1,.88,.10,.92]])
UNSAFE=np.zeros((C,W),bool); UNSAFE[2,4]=True

def stationary(P):
    vals,vecs=np.linalg.eig(P.T); v=np.real(vecs[:,np.argmin(abs(vals-1))])
    if v.sum()<0:v=-v
    v=np.maximum(v,0); return v/v.sum()
pi=stationary(Q_PRE)

def sample_rows(probs):
    u=rng.random(len(probs)); return (u[:,None]>np.cumsum(probs,1)).sum(1)

ctx=np.empty((EP,T),np.int8); obs=np.empty((EP,T),np.int8)
ctx[:,0]=sample_rows(np.tile(pi,(EP,1))); obs[:,0]=sample_rows(E[ctx[:,0]])
for t in range(1,T):
    Qt=Q_PRE if t<DRIFT else Q_POST
    ctx[:,t]=sample_rows(Qt[ctx[:,t-1]]); obs[:,t]=sample_rows(E[ctx[:,t]])

def run(name,decay=None,floor=0.0,prior_strength=30.0):
    wf=np.zeros(EP,np.int8); belief=np.tile(pi,(EP,1))
    Qhat=np.tile(Q_PRE,(EP,1,1))
    counts=np.tile(prior_strength*Q_PRE,(EP,1,1))
    welfare=np.zeros((EP,T)); correct=np.zeros((EP,T),bool); blocks=np.zeros((EP,T),bool)
    qerr=np.zeros(T); minp=np.zeros(T)

    for t in range(T):
        if t==0:
            pred=belief
        elif name=="oracle":
            Qt=Q_PRE if t<DRIFT else Q_POST
            pred=belief@Qt
        elif name=="observation":
            pred=None
        else:
            pred=np.einsum("bi,bij->bj",belief,Qhat)

        if name=="observation":
            b=np.eye(C)[obs[:,t]]
        else:
            like=E[:,obs[:,t]].T
            b=pred*like; b/=np.maximum(b.sum(1,keepdims=True),1e-15)
        inferred=b.argmax(1); correct[:,t]=(inferred==ctx[:,t])

        probs=np.zeros((EP,W))
        for c in range(C): probs+=b[:,c,None]*PCTX[c,wf]
        wf=sample_rows(probs).astype(np.int8)
        ru=UNSAFE[ctx[:,t],wf]; blocks[:,t]=ru
        wf=np.where(ru,5,wf).astype(np.int8)
        welfare[:,t]=R[ctx[:,t],wf]

        if name.startswith("adaptive") and t>0:
            like=E[:,obs[:,t]].T
            xi=prev_b[:,:,None]*Qhat*like[:,None,:]
            xi/=np.maximum(xi.sum((1,2),keepdims=True),1e-15)
            counts=decay*counts+xi
            Qhat=norm(counts)
            if floor>0:
                Qhat=norm((1-floor)*Qhat+floor*np.ones_like(Qhat)/C)

        prev_b=b.copy(); belief=b
        target=Q_PRE if t<DRIFT else Q_POST
        if name=="oracle":
            qerr[t]=0; minp[t]=target.min()
        elif name=="observation":
            qerr[t]=np.abs(Q_PRE-target).mean(); minp[t]=Q_PRE.min()
        else:
            qerr[t]=np.mean(np.abs(Qhat-target)); minp[t]=Qhat.min()

    pre=slice(100,DRIFT); early=slice(DRIFT,DRIFT+80); late=slice(T-150,T)
    return {
      "pre_welfare":float(welfare[:,pre].mean()),
      "early_post_drift_welfare":float(welfare[:,early].mean()),
      "late_post_drift_welfare":float(welfare[:,late].mean()),
      "pre_context_accuracy":float(correct[:,pre].mean()),
      "early_post_context_accuracy":float(correct[:,early].mean()),
      "late_post_context_accuracy":float(correct[:,late].mean()),
      "late_transition_mae":float(qerr[late].mean()),
      "minimum_transition_probability_seen":float(minp.min()),
      "late_hard_block_action_rate":float(blocks[:,late].mean()),
      "hard_executed_unsafe_rate":0.0,
    }

res={
 "schema":"humies.online-context-transition-adaptation.v0.3",
 "config":{"seed":SEED,"episodes":EP,"steps":T,"drift_step":DRIFT,
           "note":"Adaptive policies use posterior-weighted expected transition counts with exponential forgetting."},
 "policies":{
   "observation_only":run("observation"),
   "fixed_hmm_stale":run("fixed"),
   "adaptive_fast_unfloored":run("adaptive_fast",decay=.97,floor=0.0),
   "adaptive_fast_primitive_floor_003":run("adaptive_fast_floor",decay=.97,floor=.003),
   "adaptive_fast_primitive_floor_03":run("adaptive_fast_floor",decay=.97,floor=.03),
   "adaptive_slow_primitive_floor":run("adaptive_slow_floor",decay=.995,floor=.03),
   "oracle_model_switch":run("oracle"),
 }
}
print(json.dumps(res,indent=2,sort_keys=True))
