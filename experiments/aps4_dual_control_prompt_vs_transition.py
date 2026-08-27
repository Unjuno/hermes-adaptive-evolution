from __future__ import annotations
import json, numpy as np

SEED=20260828
rng=np.random.default_rng(SEED)
N=5000; S=5; BUDGET=8.0
SCALES=(.7,1.3,2.8,4.5)
WELFARE=np.array([1.00,.72,.78,.48,.10])
base=np.array([
 [2.2,.4,.3,.1,-.3],
 [.8,1.1,.8,.2,-.2],
 [.9,.5,1.0,.2,-.2],
 [.5,.7,.5,1.0,.0],
 [.1,.6,.5,1.1,.7],
],float)
base_logits=base[None,:,:]+rng.normal(0,.30,(N,S,S))
q0=rng.uniform(.35,.78,N)
prompt_cost=rng.uniform(.75,1.10,N)
org_cost=rng.uniform(.75,1.30,(N,S))
org_strength=rng.uniform(.45,.90,(N,S))
targets=np.array([0,0,0,0,3])
prompt_dir=np.tile(np.array([.72,.15,.18,.08,-.78]),(S,1))

def softmax(x):
    z=x-x.max(2,keepdims=True); e=np.exp(z); return e/e.sum(2,keepdims=True)

def mats(scale,q,org):
    L=base_logits+(scale*q)[:,None,None]*prompt_dir[None,:,:]
    for s in range(S):
        L[:,s,targets[s]] += org[:,s]*org_strength[:,s]
        L[:,s,4] -= .40*org[:,s]*org_strength[:,s]
    return softmax(L)

def util(scale,q,org):
    P=mats(scale,q,org)
    A=np.transpose(P,(0,2,1))-np.eye(S)[None,:,:]
    A[:,-1,:]=1.0
    b=np.zeros((N,S)); b[:,-1]=1
    pi=np.linalg.solve(A,b[...,None])[...,0]
    return pi@WELFARE

def q_up(q): return np.minimum(.985,q+.11*(1-q))
def org_up(org,j,mask=None):
    z=org.copy()
    if mask is None: z[:,j]=np.minimum(1.5,z[:,j]+.22)
    else: z[mask,j]=np.minimum(1.5,z[mask,j]+.22)
    return z

def run(scale,strategy):
    q=q0.copy(); org=np.zeros((N,S)); rem=np.full(N,BUDGET)
    n_prompt=np.zeros(N,int); n_org=np.zeros(N,int); n_coupled=np.zeros(N,int)
    u_initial=util(scale,q,org)
    for step in range(20):
        active=rem>=.70
        if not active.any(): break
        baseu=util(scale,q,org)
        qp=q_up(q)
        pg=(util(scale,qp,org)-baseu)/prompt_cost
        lg=np.empty((N,S))
        for j in range(S): lg[:,j]=(util(scale,q,org_up(org,j))-baseu)/org_cost[:,j]
        bestj=lg.argmax(1); bestg=lg[np.arange(N),bestj]
        op=np.full(N,3,int)
        if strategy=='prompt_only': op[(active)&(prompt_cost<=rem)]=0
        elif strategy=='transition_only':
            feasible=org_cost[np.arange(N),bestj]<=rem
            op[active&feasible]=1
        elif strategy=='alternating':
            if step%2==0: op[active&(prompt_cost<=rem)]=0
            else:
                feasible=org_cost[np.arange(N),bestj]<=rem; op[active&feasible]=1
        elif strategy=='prompt_first_3':
            if step<3: op[active&(prompt_cost<=rem)]=0
            else:
                feasible=org_cost[np.arange(N),bestj]<=rem; op[active&feasible]=1
        elif strategy=='dual_axis_adaptive':
            pc_ok=prompt_cost<=rem
            oc=org_cost[np.arange(N),bestj]; oc_ok=oc<=rem
            choosep=pc_ok & ((pg>=bestg)|(~oc_ok))
            chooseo=oc_ok & ((bestg>pg)|(~pc_ok))
            op[active&choosep]=0; op[active&chooseo]=1
        elif strategy=='coupled_every_change':
            c=prompt_cost+org_cost[np.arange(N),bestj]
            op[active&(c<=rem)]=2
        else: raise ValueError(strategy)
        sel=op==0
        if sel.any(): q[sel]=q_up(q[sel]); rem[sel]-=prompt_cost[sel]; n_prompt[sel]+=1
        sel=op==1
        if sel.any():
            ids=np.where(sel)[0]; jj=bestj[sel]
            for j in range(S):
                m=sel&(bestj==j); org[m,j]=np.minimum(1.5,org[m,j]+.22)
            rem[sel]-=org_cost[ids,jj]; n_org[sel]+=1
        sel=op==2
        if sel.any():
            ids=np.where(sel)[0]; jj=bestj[sel]
            q[sel]=q_up(q[sel])
            for j in range(S):
                m=sel&(bestj==j); org[m,j]=np.minimum(1.5,org[m,j]+.22)
            rem[sel]-=(prompt_cost[sel]+org_cost[ids,jj]); n_coupled[sel]+=1
        if np.all(op==3): break
    fin=util(scale,q,org)
    return {'mean_final_welfare':float(fin.mean()),'mean_gain':float((fin-u_initial).mean()),'mean_prompt_updates':float(n_prompt.mean()),'mean_transition_updates':float(n_org.mean()),'mean_coupled_updates':float(n_coupled.mean()),'mean_budget_used':float(np.mean(BUDGET-rem))}

strategies=('prompt_only','transition_only','alternating','prompt_first_3','coupled_every_change','dual_axis_adaptive')
grid={}
for scale in SCALES: grid[str(scale)]={s:run(scale,s) for s in strategies}
res={'schema':'humies.agent-prompt-dual-control-separation.v0.1','config':{'seed':SEED,'systems':N,'budget':BUDGET,'prompt_leverage_scales':list(SCALES)},'grid':grid}
print(json.dumps(res,indent=2,sort_keys=True))
