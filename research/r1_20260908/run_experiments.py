"""Equal-evidence weak effects and task-dependence stress; offline only."""
from __future__ import annotations
import argparse, hashlib, json, math, os, platform, sys, time
from pathlib import Path
import numpy as np
from scipy.stats import norm,t
from scipy.special import logsumexp
SEED=2026090801
BETS=np.array([0.,.02,.05,.1,.2,.4,.8]);ALPHA=.05;Z=norm.ppf(.95)
def wilson(k,n):
 z=norm.ppf(.975);p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return [float(c-h),float(c+h)]
def zs(x):return x.mean(axis=-1)/np.maximum(x.std(axis=-1,ddof=1)/np.sqrt(x.shape[-1]),1e-14)
def rates(dec):return {m:{'promotions':int(v.sum()),'replicates':len(v),'rate':float(v.mean()),'wilson95':wilson(int(v.sum()),len(v))} for m,v in dec.items()}
def betting(d,repeat=1):
 logs=np.zeros((len(d),len(BETS)));first=np.full(len(d),d.shape[1]*repeat,int);cross=np.zeros(len(d),bool)
 for k in range(d.shape[1]):
  inc=np.log1p(d[:,k,None]*BETS)
  for j in range(repeat):
   logs+=inc;hit=logsumexp(logs,axis=1)-math.log(len(BETS))>=math.log(1/ALPHA)
   first[hit&~cross]=k*repeat+j+1;cross|=hit
 return cross,first

def exact_weak(reps):
 out=[];nh=350
 for ci,mu in enumerate([-.04,0.,.02,.04,.08,.15,.30]):
  rng=np.random.default_rng(SEED+10000+ci);x=rng.normal(mu,1.,(reps,2*nh));a=zs(x[:,:nh]);b=zs(x[:,nh:]);p=zs(x)
  dec={'two_separate_5pct':(a>Z)&(b>Z),'pooled_fixed_5pct':p>Z,'peek_twice_naive_5pct':(a>Z)|(p>Z),'peek_twice_bonferroni':(a>norm.ppf(.975))|(p>norm.ppf(.975))}
  out.append({'standardized_mean':mu,'independent_observations':2*nh,'theory_known_variance':{'two_separate_5pct':float(norm.sf(Z-mu*np.sqrt(nh))**2),'pooled_fixed_5pct':float(norm.sf(Z-mu*np.sqrt(2*nh)))},'methods':rates(dec)})
 return out

def world(rng,n,amp):
 z=rng.choice(np.array([-1.,1.]),(n,2));s=np.repeat(z,2,1)+rng.normal(0,.85,(n,4));x=rng.normal(size=(n,2));q=rng.uniform(.2,.85,(n,2))
 mu=.018*z[:,0]+.008*x[:,1]-.005*q[:,1];tau=.006*(1-q[:,0])+.003*x[:,0]+amp*z[:,0]*z[:,1]
 a=rng.integers(0,2,n);y=mu+a*tau+rng.normal(0,.025,n)
 xb=np.c_[np.ones(n),q,x,s];h=np.tanh(1.2*np.c_[(s[:,0]+s[:,1])/2,(s[:,2]+s[:,3])/2])
 return {'xb':xb,'xc':np.c_[xb,h,h[:,0]*h[:,1]],'a':a,'y':y},{'tau':tau}
def fit(obs):
 py=np.where(obs['a']==1,2*obs['y'],-2*obs['y']);bs=[]
 for name in ('xb','xc'):
  x=obs[name];bs.append(np.linalg.solve(x.T@x+.8*np.eye(x.shape[1]),x.T@py))
 return tuple(bs)
def policies(obs,bs):return tuple((obs[name]@b>0).astype(int) for name,b in zip(('xb','xc'),bs))
def learner_weak(reps):
 out=[]
 for ci,amp in enumerate([0.,.002,.006,.012,.04]):
  rec=[]
  for rep in range(reps):
   ss=np.random.SeedSequence([SEED,20,ci,rep]);rd,rg,rt=map(np.random.default_rng,ss.spawn(3))
   disc,_=world(rd,800,amp);bs=fit(disc);sel,_=world(rg,700,amp);pb,pc=policies(sel,bs)
   d=2*sel['y']*((sel['a']==pc).astype(int)-(sel['a']==pb).astype(int));za=float(zs(d[:350]));zb=float(zs(d[350:]));zp=float(zs(d))
   dec={'two_separate_5pct':za>Z and zb>Z,'pooled_fixed_5pct':zp>Z,'peek_twice_naive_5pct':za>Z or zp>Z,'peek_twice_bonferroni':za>norm.ppf(.975) or zp>norm.ppf(.975)}
   fixed_hash=hashlib.sha256(b''.join(b.tobytes() for b in bs)).hexdigest()
   test,truth=world(rt,20000,amp);p0,p1=policies(test,bs);tau=truth['tau'];r0=np.abs(tau)*(p0!=(tau>0));r1=np.abs(tau)*(p1!=(tau>0))
   rec.append({'seed_parts':[SEED,20,ci,rep],'artifact_hash':fixed_hash,'base_regret':float(r0.mean()),'candidate_regret':float(r1.mean()),'evaluation_gain_se':float((r0-r1).std(ddof=1)/np.sqrt(len(tau))),'decisions':{k:bool(v) for k,v in dec.items()},'z_halves':[za,zb],'z_pooled':zp})
  methods={}
  for name in rec[0]['decisions']:
   k=sum(r['decisions'][name] for r in rec);final=[r['candidate_regret'] if r['decisions'][name] else r['base_regret'] for r in rec]
   methods[name]={'promotions':k,'replicates':reps,'promotion_rate':k/reps,'wilson95':wilson(k,reps),'mean_final_regret':float(np.mean(final)),'promoted_eval_harmful_point_estimates':sum(r['decisions'][name] and r['candidate_regret']>r['base_regret'] for r in rec)}
  diff=np.array([(r['candidate_regret']-r['base_regret'])*(int(r['decisions']['pooled_fixed_5pct'])-int(r['decisions']['two_separate_5pct'])) for r in rec]);se=diff.std(ddof=1)/np.sqrt(reps);q=t.ppf(.975,reps-1)
  out.append({'effect_amplitude':amp,'reps':reps,'methods':methods,'base_mean_regret':float(np.mean([r['base_regret'] for r in rec])),'pooled_minus_two_regret':{'mean':float(diff.mean()),'ci95_t':[float(diff.mean()-q*se),float(diff.mean()+q*se)]},'records':rec})
 return out

def bounded(reps,n,duplicate=False):
 out=[]
 for ci,mu in enumerate([0.] if duplicate else [0.,.01,.03,.06,.12]):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,30+int(duplicate),ci]));u=rng.random((reps,n));v=.3
  d=np.where(u<(v+mu)/2,1.,np.where(u<v,-1.,0.));half=n//2
  dec={'two_separate_5pct':(zs(d[:,:half])>Z)&(zs(d[:,half:])>Z),'pooled_fixed_5pct':zs(d)>Z}
  ep,first=betting(d);dec['anytime_betting']=ep;dec['repeated_naive_5pct']=np.logical_or.reduce([zs(d[:,:k])>Z for k in range(50,n+1,50)])
  extra={'anytime_betting':{'mean_consumed_units':float(first.mean()),'median_consumed_units':float(np.median(first))}}
  if duplicate:
   bad,_=betting(d,repeat=8);dec['replayed_rows_as_new_betting']=bad;sx=d.sum(1)*8;ss=(d*d).sum(1)*8;count=n*8;mean=sx/count;var=(ss-count*mean*mean)/(count-1)
   dec['replayed_rows_as_new_z']=mean/np.maximum(np.sqrt(var/count),1e-14)>Z;extra.update(actual_unique_tasks=n,invalid_repeated_rows=n*8)
  out.append({'true_policy_gain':mu,'disagreement_mass':v,'units':n,'methods':rates(dec),'extra':extra})
 return out

def main():
 a=argparse.ArgumentParser();a.add_argument('--stage',choices=['weak','bounded','all'],default='all');a.add_argument('--output',type=Path,required=True);args=a.parse_args();start=time.perf_counter()
 res={'schema':'hermes.r1-equal-budget-cluster-evidence.v1','seed':SEED,'environment':{'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}},'authority':'offline_research_only','execution_authorized':False}
 if args.stage in ['weak','all']:res.update(exact_gaussian=exact_weak(10000),learned_policy_weak=learner_weak(160))
 if args.stage in ['bounded','all']:res.update(bounded_iid=bounded(3000,1000),replay_attack=bounded(3000,200,True))
 res['wall_seconds']=time.perf_counter()-start;args.output.write_text(json.dumps(res,indent=2),encoding='utf-8')
 for k in ['exact_gaussian','learned_policy_weak','bounded_iid','replay_attack']:
  if k in res:print(k,json.dumps([{kk:vv for kk,vv in x.items() if kk!='records'} for x in res[k]],indent=2))
if __name__=='__main__':main()
