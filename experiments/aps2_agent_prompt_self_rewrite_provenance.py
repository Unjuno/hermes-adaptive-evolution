from __future__ import annotations
import json, numpy as np
SEED=20260828; EP=12000; T=500
base_rng=np.random.default_rng(SEED); cap=base_rng.uniform(.78,.92,EP); q0=base_rng.uniform(.48,.72,EP)

def run(policy):
    rng=np.random.default_rng(SEED+999)
    q=q0.copy(); fidelity=np.ones(EP); patches=np.zeros(EP,int); updates=np.zeros(EP,int)
    success=np.zeros(EP,int); semantic=np.zeros(EP,int); pf=np.zeros(EP,int); of=np.zeros(EP,int); acc=np.zeros(EP,int)
    if policy=='one_time': q=np.minimum(.96,q+.18*(1-q)); updates+=1
    for t in range(T):
        u_prompt=rng.random(EP); u_other=rng.random(EP); u_detector=rng.random(EP); u_sem=rng.random(EP); u_rewrite=rng.random(EP)
        complexity=np.where(patches>0,np.maximum(.90,1-.0015*patches),1.0); eq=np.clip(q*complexity,0,1)
        p_prompt=.30*(1-eq); p_other=.055+.10*(1-cap); p_sem=.32*(1-fidelity)
        f_prompt=u_prompt<p_prompt; f_other=u_other<p_other; f_sem=u_sem<p_sem; fail=f_prompt|f_other|f_sem
        success+=(~fail); semantic+=f_sem; pf+=f_prompt; of+=f_other
        detected=fail&((f_prompt&(u_detector<.78))|((~f_prompt)&(u_detector<.07)))
        if policy in ('none','one_time'): do=np.zeros(EP,bool)
        elif policy in ('destructive_any_failure','immutable_any_failure'): do=fail
        elif policy in ('gated_destructive','gated_immutable'): do=detected
        elif policy=='batched_immutable': acc+=detected.astype(int); do=acc>=4; acc[do]=0
        else: raise ValueError(policy)
        if np.any(do):
            q[do]=np.minimum(.985,q[do]+.095*(1-q[do])); updates[do]+=1
            if policy in ('destructive_any_failure','gated_destructive'):
                drift=.002+.012*u_rewrite[do]; fidelity[do]*=(1-drift)
            else: patches[do]+=1
    return {'mean_success_rate':float(np.mean(success/T)),'mean_final_clarity':float(q.mean()),'mean_final_fidelity':float(fidelity.mean()),'mean_updates':float(updates.mean()),'mean_patches':float(patches.mean()),'semantic_failure_rate':float(semantic.sum()/(EP*T)),'prompt_failure_rate':float(pf.sum()/(EP*T)),'other_failure_rate':float(of.sum()/(EP*T)),'fraction_fidelity_below_0_8':float(np.mean(fidelity<.8))}
policies=('none','one_time','destructive_any_failure','immutable_any_failure','gated_destructive','gated_immutable','batched_immutable')
res={'schema':'humies.agent-prompt-self-rewrite-provenance.v0.2','config':{'seed':SEED,'episodes':EP,'steps':T,'detector_recall':.78,'detector_false_positive':.07,'note':'Synthetic prompt clarity/fidelity model; immutable policies preserve original prompt and add versioned patches.'},'summary':{p:run(p) for p in policies}}
print(json.dumps(res,indent=2,sort_keys=True))
