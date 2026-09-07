"""Follow-up fixed after weak-signal results: match size AND alpha, then family multiplicity."""
import json, math
from pathlib import Path
import numpy as np
from scipy.stats import norm
from scipy.special import logsumexp
import run_experiments as core
SEED=2026090817
out={'schema':'hermes.r1-followup-risk-matching.v1','seed':SEED,'phase':'new_seed_confirmation',
     'reason':'two 5% halves have joint 0.25% null risk under common fixed mean; match this with pooled test'}
rows=[]
for i,mu in enumerate([0.,.02,.04,.08,.15]):
 rng=np.random.default_rng(SEED+i);x=rng.normal(mu,1,(10000,700));z1=core.zs(x[:,:350]);z2=core.zs(x[:,350:]);zp=core.zs(x)
 rows.append({'mean':mu,'same_nominal_alpha':.0025,'same_n':700,'methods':core.rates({'two_halves_each_5pct':(z1>norm.ppf(.95))&(z2>norm.ppf(.95)),'pooled_matched_0_25pct':zp>norm.ppf(.9975)})})
out['risk_matched']=rows
# Family comparison: same simulations, a prespecified family of 20 candidates.
reps=2000;m=20;n=200;rng=np.random.default_rng(SEED+100)
u=rng.random((reps*m,n));d=np.where(u<.15,1.,np.where(u<.30,-1.,0.));logs=np.zeros((reps*m,len(core.BETS)))
hit_unadjusted=np.zeros(reps*m,bool);hit_family=np.zeros(reps*m,bool)
for k in range(n):
 logs+=np.log1p(d[:,k,None]*core.BETS)
 le=logsumexp(logs,axis=1)-math.log(len(core.BETS))
 hit_unadjusted|=le>=math.log(20);hit_family|=le>=math.log(m/.05)
out['candidate_family_null']={'family_size':m,'unique_units_per_candidate':n,'methods':core.rates({'unadjusted_each_5pct':hit_unadjusted.reshape(reps,m).any(1),'allocated_family_total_5pct':hit_family.reshape(reps,m).any(1)})}
Path(__file__).parents[1].joinpath('results/followup.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
