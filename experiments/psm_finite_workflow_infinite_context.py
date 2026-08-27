from __future__ import annotations
import json
import numpy as np

SEED=20260827
rng=np.random.default_rng(SEED)

CONTEXTS=("normal","ambiguous","risky")
WORKFLOWS=("ingest","tune","audit","specialist","execute","recover")
C,W=3,6

# Persistent but primitive hidden context process.
Q=np.array([
 [.96,.03,.01],
 [.04,.92,.04],
 [.02,.08,.90],
],float)

BASE=np.array([
 [.05,.60,.15,.10,.05,.05],
 [.05,.10,.35,.25,.20,.05],
 [.05,.10,.15,.25,.35,.10],
 [.05,.10,.20,.10,.45,.10],
 [.05,.10,.10,.05,.60,.10],
 [.20,.25,.20,.10,.10,.15],
],float)

def norm(M):
    M=np.maximum(M,1e-12)
    return M/M.sum(1,keepdims=True)

def kernel(c):
    M=BASE.copy()
    if c==0:
        M[:,4]*=1.65; M[:,3]*=.60; M[:,5]*=.65
    elif c==1:
        M[:,1]*=1.30; M[:,2]*=1.45; M[:,3]*=1.65; M[:,4]*=.60
    else:
        M[:,2]*=1.85; M[:,3]*=1.30; M[:,4]*=.30; M[:,5]*=1.90
    eps=.012
    return norm((1-eps)*norm(M)+eps*np.ones_like(M)/W)

PCTX=np.stack([kernel(c) for c in range(C)])

def stationary(P):
    vals,vecs=np.linalg.eig(P.T)
    v=np.real(vecs[:,np.argmin(abs(vals-1))])
    if v.sum()<0:v=-v
    v=np.maximum(v,0)
    return v/v.sum()

def primitive_exp(P,maxk=100):
    B=P.copy()
    for k in range(1,maxk+1):
        if np.all(B>1e-14): return k
        B=B@P
    return None

pi_c=stationary(Q)
PBLIND=np.tensordot(pi_c,PCTX,axes=(0,0))

R=np.array([
 [.45,.65,.68,.58,1.00,.42],
 [.40,.83,.90,1.00,.58,.55],
 [.32,.64,1.00,.88,.10,.92],
])

UNSAFE=np.zeros((C,W),bool); UNSAFE[2,4]=True

# Deliberately noisy telemetry: current observation alone is imperfect;
# persistent hidden context makes history potentially useful.
E=np.array([
 [.62,.28,.10],
 [.25,.55,.20],
 [.12,.28,.60],
],float)

# Joint finite Markov chain over (hidden context, workflow) for oracle controller.
K=np.zeros((C*W,C*W))
for c in range(C):
    for w in range(W):
        i=c*W+w
        for cp in range(C):
            for wp in range(W):
                K[i,cp*W+wp]=Q[c,cp]*PCTX[cp,w,wp]
pi_joint=stationary(K)
eig=np.linalg.eigvals(K)
mods=np.sort(np.abs(eig))[::-1]
spectral_gap=float(1-mods[1])

# Long one-trajectory ergodic convergence.
T_LONG=800_000
checkpoints=(1_000,5_000,20_000,100_000,400_000,800_000)
state=int(rng.integers(C*W)); counts=np.zeros(C*W,dtype=np.int64); conv={}
for t in range(1,T_LONG+1):
    counts[state]+=1
    u=rng.random()
    state=int(np.searchsorted(np.cumsum(K[state]),u,side="right"))
    if t in checkpoints:
        emp=counts/counts.sum()
        conv[str(t)]={
          "l1_occupancy_error":float(np.abs(emp-pi_joint).sum()),
          "max_abs_occupancy_error":float(np.max(np.abs(emp-pi_joint))),
        }

# Paired hidden worlds.
EP,T=24000,320
ctx=np.empty((EP,T),np.int8); obs=np.empty((EP,T),np.int8)
def sample_rows(probs):
    u=rng.random(len(probs))
    return (u[:,None]>np.cumsum(probs,axis=1)).sum(1)

ctx[:,0]=sample_rows(np.tile(pi_c,(EP,1)))
obs[:,0]=sample_rows(E[ctx[:,0]])
for t in range(1,T):
    ctx[:,t]=sample_rows(Q[ctx[:,t-1]])
    obs[:,t]=sample_rows(E[ctx[:,t]])

Qwrong=np.array([
 [.60,.20,.20],
 [.20,.60,.20],
 [.20,.20,.60],
],float)

def controller(name, mismatch=0.0):
    wf=np.zeros(EP,np.int8)
    welfare=np.zeros(EP); blocks=np.zeros(EP,np.int32); switches=np.zeros(EP,np.int32)
    raw_unsafe_actions=0
    belief=np.tile(pi_c,(EP,1))
    context_correct=0
    Qm=(1-mismatch)*Q+mismatch*Qwrong

    for t in range(T):
        c=ctx[:,t]
        if name in ("hmm","hmm_stale"):
            if t: belief=belief@Qm
            belief*=E[:,obs[:,t]].T
            belief/=np.maximum(belief.sum(1,keepdims=True),1e-15)
            inferred=belief.argmax(1)
            context_correct+=int(np.sum(inferred==c))
        elif name=="observation":
            inferred=obs[:,t]
            context_correct+=int(np.sum(inferred==c))

        if name=="blind":
            probs=PBLIND[wf]
        elif name=="observation":
            probs=PCTX[inferred,wf]
        elif name=="oracle":
            probs=PCTX[c,wf]
        elif name in ("hmm","hmm_stale"):
            probs=np.zeros((EP,W))
            for cc in range(C):
                probs+=belief[:,cc,None]*PCTX[cc,wf]
        elif name=="deterministic_cycle":
            nxt=(wf+1)%W
            probs=np.eye(W)[nxt]
        else:
            raise ValueError(name)

        nxt=sample_rows(probs).astype(np.int8)
        switches+=(nxt!=wf); wf=nxt
        ru=UNSAFE[c,wf]
        raw_unsafe_actions+=int(ru.sum())
        blocks+=ru.astype(np.int32)
        wf=np.where(ru,5,wf).astype(np.int8)  # hard runtime external to controller
        welfare+=R[c,wf]

    return {
      "mean_welfare":float(np.mean(welfare/T)),
      "raw_unsafe_action_rate":float(raw_unsafe_actions/(EP*T)),
      "mean_hard_blocks_per_episode":float(blocks.mean()),
      "hard_executed_unsafe_rate":0.0,
      "mean_workflow_switches_per_episode":float(switches.mean()),
      "context_inference_accuracy":None if name in ("blind","oracle","deterministic_cycle") else float(context_correct/(EP*T)),
    }

controllers={
 "deterministic_cycle":controller("deterministic_cycle"),
 "context_blind":controller("blind"),
 "observation_only":controller("observation"),
 "hmm_belief":controller("hmm"),
 "hmm_stale_50pct":controller("hmm_stale",.50),
 "oracle_context":controller("oracle"),
}

# Show that workflow alone is not an exact Markov sufficient statistic under persistent hidden context.
EP_M,T_M=30000,150
c=sample_rows(np.tile(pi_c,(EP_M,1))).astype(np.int8)
w=np.zeros(EP_M,np.int8); prev=None
pairs=np.zeros((W,W),np.int64); triples=np.zeros((W,W,W),np.int64)
for t in range(T_M):
    cp=sample_rows(Q[c]).astype(np.int8)
    wp=sample_rows(PCTX[cp,w]).astype(np.int8)
    pairs+=np.bincount(w.astype(int)*W+wp.astype(int),minlength=W**2).reshape(W,W)
    if prev is not None:
        flat=prev.astype(int)*W*W+w.astype(int)*W+wp.astype(int)
        triples+=np.bincount(flat,minlength=W**3).reshape(W,W,W)
    prev=w.copy(); w=wp; c=cp
p1=pairs/np.maximum(pairs.sum(1,keepdims=True),1)
p2=triples/np.maximum(triples.sum(2,keepdims=True),1)
dev=[]; weights=[]
for a in range(W):
    for b in range(W):
        n=triples[a,b].sum()
        if n>200:
            dev.append(np.abs(p2[a,b]-p1[b]).sum()); weights.append(n)
memory_dev=float(np.average(dev,weights=weights))

result={
 "schema":"humies.finite-workflow-infinite-contextual-trajectory.v0.2",
 "config":{"seed":SEED,"contexts":list(CONTEXTS),"workflows":list(WORKFLOWS),
           "long_trajectory_steps":T_LONG,"paired_episodes":EP,"episode_steps":T},
 "structural":{
   "finite_augmented_state_count":C*W,
   "context_kernel_primitive_exponent":primitive_exp(Q),
   "workflow_kernel_primitive_exponents":{CONTEXTS[c]:primitive_exp(PCTX[c]) for c in range(C)},
   "joint_chain_primitive_exponent":primitive_exp(K),
   "joint_chain_spectral_gap":spectral_gap,
   "oracle_joint_stationary_welfare":float(sum(pi_joint[c*W+w]*R[c,w] for c in range(C) for w in range(W))),
 },
 "infinite_trajectory_convergence":conv,
 "controllers":controllers,
 "context_memory_test":{
   "weighted_l1_next_workflow_change_given_previous_workflow":memory_dev,
   "interpretation":"If workflow alone were an exact first-order Markov sufficient statistic, conditioning additionally on the previous workflow would not change next-workflow probabilities except sampling noise."
 }
}
print(json.dumps(result,indent=2,sort_keys=True))
