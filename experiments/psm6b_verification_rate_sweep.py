from __future__ import annotations
import json, numpy as np

SEED=20260830
rng=np.random.default_rng(SEED)
C,W=3,6
Q=np.array([[.975,.020,.005],[.015,.965,.020],[.006,.024,.970]],float)
R=np.array([[.48,.65,.70,.58,1,.45],[.42,.82,.92,1,.56,.58],[.34,.62,1,.88,.08,.94]])
SUP=np.array([
 [.18,.38,.15,.10,.10,.09],[.08,.22,.27,.20,.16,.07],
 [.07,.10,.30,.22,.18,.13],[.07,.10,.18,.22,.31,.12],
 [.06,.08,.12,.08,.55,.11],[.18,.20,.17,.11,.12,.22]],float)
SUP/=SUP.sum(1,keepdims=True)
EP,T=1000,800
UPDATE=5; ETA=.28; FLOOR=.02; SWITCH=.025; SD=.14; START=180; P=.75
POS=1.6; NEG=1.0
RATES=(.02,.05,.10,.20,.40)

reg=np.empty((EP,T),np.int8); reg[:,0]=rng.integers(0,C,EP)
for t in range(1,T):
    u=rng.random(EP); reg[:,t]=(u[:,None]>np.cumsum(Q[reg[:,t-1]],1)).sum(1)
noise=rng.normal(0,SD,(EP,T)); pu=rng.random((EP,T)); vu=rng.random((EP,T))

def sm(x):
    z=x-x.max(1,keepdims=True); e=np.exp(z); return e/e.sum(1,keepdims=True)

def run(rate,policy):
    logits=np.zeros((EP,C,W)); base=np.full((EP,C),.67)
    sums=np.zeros((EP,C,W)); counts=np.zeros((EP,C,W)); quarantine=np.zeros((EP,C,W),bool)
    wf=np.zeros(EP,np.int8); welfare=np.zeros(EP); blocks=0; poison_used=0; qevents=0; prefs=[]
    for t in range(T):
        c=reg[:,t]; pref=sm(logits[np.arange(EP),c])
        row=SUP[wf]*(.15+.85*pref*W); row/=row.sum(1,keepdims=True)
        row=(1-FLOOR)*row+FLOOR*SUP[wf]; row/=row.sum(1,keepdims=True)
        u=rng.random(EP); prop=(u[:,None]>np.cumsum(row,1)).sum(1).astype(np.int8)
        unsafe=(c==2)&(prop==4); exe=np.where(unsafe,5,prop).astype(np.int8); blocks+=int(unsafe.sum())
        truth=R[c,exe]-SWITCH*(exe!=wf); welfare+=truth
        raw=R[c,prop]-SWITCH*(prop!=wf)+noise[:,t]
        elig=(t>=START)&(c==2)&(pu[:,t]<P)
        pos=elig&(prop==4); neg=elig&((prop==2)|(prop==5)); poisoned=pos|neg
        observed=raw+POS*pos-NEG*neg
        audit=vu[:,t]<rate

        learn_reward=np.where(audit,truth,observed)
        target=np.where(audit,exe,prop).astype(np.int8)
        mask=np.ones(EP,bool)
        if policy=="quarantine":
            disagreement=audit&(np.abs(observed-truth)>.45)
            rr=np.where(disagreement)[0]
            if len(rr):
                quarantine[rr,c[rr],prop[rr]]=True; qevents+=len(rr)
            mask=~quarantine[np.arange(EP),c,prop]
        poison_used+=int(np.sum(poisoned&(~audit)&mask))
        rr=np.where(mask)[0]
        if len(rr):
            tt=target[rr]; sums[rr,c[rr],tt]+=learn_reward[rr]; counts[rr,c[rr],tt]+=1
        wf=exe
        if (t+1)%UPDATE==0:
            means=np.divide(sums,np.maximum(counts,1)); sig=(means-base[:,:,None])*(counts>0)
            logits+=ETA*sig; logits*=.995
            tot=counts.sum(2); bav=np.divide((means*counts).sum(2),np.maximum(tot,1))
            base=np.where(tot>0,.9*base+.1*bav,base)
            if policy=="quarantine": logits=np.where(quarantine,np.minimum(logits,0),logits)
            sums.fill(0); counts.fill(0)
            if t>=START: prefs.append(float(sm(logits[:,2])[:,4].mean()))
    return {
      "mean_welfare":float(np.mean(welfare/T)),
      "hard_block_action_rate":float(blocks/(EP*T)),
      "late_risky_execute_preference":float(np.mean(prefs[-60:])),
      "poisoned_unverified_samples_per_episode":float(poison_used/EP),
      "quarantine_events_per_episode":float(qevents/EP),
    }

grid={}
for rate in RATES:
    grid[str(rate)]={
      "verified_correct":run(rate,"correct"),
      "quarantine":run(rate,"quarantine"),
    }
res={"schema":"humies.psm6b-verification-rate-sweep.v0.1",
     "config":{"seed":SEED,"episodes":EP,"steps":T,"verify_rates":RATES},
     "grid":grid}
print(json.dumps(res,indent=2,sort_keys=True))
