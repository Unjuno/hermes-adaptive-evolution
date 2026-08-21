from __future__ import annotations
import argparse, json, random, statistics, math
from dataclasses import dataclass

@dataclass
class Candidate:
    name: str
    center: float
    width: float
    true_quality: float


def env_optimum(t:int, shift_t:int)->float:
    return -0.6 if t < shift_t else 0.7


def reward(c:Candidate, t:int, shift_t:int, rare:bool, rng:random.Random)->float:
    opt = env_optimum(t, shift_t)
    dist = abs(c.center - opt)
    # common contexts tolerate hacks/local fits; rare contexts expose misspecification strongly
    scale = 0.95 if not rare else 1.8
    mu = max(0.0, 1.0 - scale*dist)
    # narrow candidates can look deceptively good in common contexts, but fail rare probes
    if not rare:
        mu += 0.12*max(0.0, 0.35-c.width)
    else:
        mu -= 0.30*max(0.0, 0.35-c.width)
    mu = min(1.0,max(0.0,mu))
    return min(1.0,max(0.0,rng.gauss(mu,0.08)))


def make_candidate(rng:random.Random, around:float|None=None, pressure:float=1.0, idx:int=0)->Candidate:
    if around is None:
        center = rng.uniform(-1.0,1.0)
    else:
        sigma = min(0.9, 0.15 + 0.35*pressure)
        center = max(-1.0,min(1.0,rng.gauss(around,sigma)))
    width = rng.uniform(0.15,0.8)
    return Candidate(f'c{idx}',center,width,0.0)


def run(seed:int, mode:str, steps:int=360, shift_t:int=180, n_agents:int=40,
        initial_pool:int=3, verify_prob:float=0.10, rare_prob:float=0.06,
        transmission_rate:float=0.20, contradiction_threshold:float=0.22,
        generate_threshold:int=3, max_pool:int=18)->dict:
    rng=random.Random(seed)
    pool=[make_candidate(rng, idx=i) for i in range(initial_pool)]
    scores={c.name:0.0 for c in pool}
    weights={c.name:1e-6 for c in pool}
    counts={c.name:0 for c in pool}
    half_life={c.name:50.0 for c in pool}
    contrad={c.name:0 for c in pool}
    agents=[rng.choice(pool).name for _ in range(n_agents)]
    generated=0
    history=[]
    best_dist=[]

    def cdict(): return {c.name:c for c in pool}

    for t in range(steps):
        cmap=cdict()
        # decay evidence
        for name in list(scores):
            hl=half_life[name]
            d=0.5**(1.0/max(hl,1e-9)); scores[name] *= d; weights[name] *= d

        # local experience and optional independent rare verification
        for i in range(n_agents):
            name=agents[i]; c=cmap[name]
            rare=rng.random()<rare_prob
            r=reward(c,t,shift_t,rare,rng)
            scores[name]+=r; weights[name]+=1.0; counts[name]+=1
            if rare:
                if r<contradiction_threshold:
                    contrad[name]+=1
                    if mode in ('adaptive_generate','adaptive_no_generate'):
                        half_life[name]=max(5.0,half_life[name]*0.45)
                elif r>0.55 and mode in ('adaptive_generate','adaptive_no_generate'):
                    half_life[name]=min(180.0,half_life[name]*1.05)

            if rng.random()<verify_prob:
                vr=reward(c,t,shift_t,True,rng)
                scores[name]+=2.2*vr; weights[name]+=2.2
                counts[name]+=1
                if vr<contradiction_threshold:
                    contrad[name]+=1
                    if mode in ('adaptive_generate','adaptive_no_generate'):
                        half_life[name]=max(5.0,half_life[name]*0.35)
                elif vr>0.55 and mode in ('adaptive_generate','adaptive_no_generate'):
                    half_life[name]=min(180.0,half_life[name]*1.08)

        # generation pressure from repeated contradiction
        if mode=='adaptive_generate' and len(pool)<max_pool:
            bad=[n for n,v in contrad.items() if v>=generate_threshold]
            if bad:
                # generate near current population weighted center, but with pressure-controlled diversity
                cmap=cdict()
                centers=[cmap[n].center for n in agents]
                around=statistics.mean(centers) if centers else 0.0
                pressure=min(2.0, statistics.mean(contrad[n] for n in bad)/generate_threshold)
                newc=make_candidate(rng,around=around,pressure=pressure,idx=initial_pool+generated)
                pool.append(newc); scores[newc.name]=0.15; weights[newc.name]=0.25; counts[newc.name]=0; half_life[newc.name]=30.0; contrad[newc.name]=0
                # exploratory seeding to a few agents
                for j in rng.sample(range(n_agents), k=max(1,n_agents//10)):
                    agents[j]=newc.name
                generated+=1
                for n in bad:
                    contrad[n]=0

        # random propagation as weak evidence
        cmap=cdict()
        for _ in range(max(1,int(n_agents*transmission_rate))):
            s,tgt=rng.sample(range(n_agents),2)
            proposed=agents[s]
            scores[proposed]+=0.10; weights[proposed]+=0.20
            # adoption is mostly evidence-based, not pure copying
            est=lambda n: scores[n]/max(weights[n],1e-9)
            if est(proposed) > est(agents[tgt]) + 0.03:
                agents[tgt]=proposed

        # individual choice with small exploration
        names=list(scores)
        for i in range(n_agents):
            if rng.random()<0.02:
                agents[i]=rng.choice(names)
            else:
                current=agents[i]
                sample=rng.sample(names,k=min(4,len(names)))
                best=max(sample+[current], key=lambda n:scores[n]/max(weights[n],1e-9))
                agents[i]=best

        cmap=cdict(); opt=env_optimum(t,shift_t)
        frac_good=sum(abs(cmap[n].center-opt)<=0.20 for n in agents)/n_agents
        history.append(frac_good)
        best_dist.append(min(abs(c.center-opt) for c in pool))

    adaptation_delay=None
    for t in range(shift_t,steps-9):
        if min(history[t:t+10])>=0.75:
            adaptation_delay=t-shift_t; break
    return {
        'seed':seed,'mode':mode,'generated':generated,
        'final_good':statistics.mean(history[-50:]),
        'adaptation_delay':adaptation_delay if adaptation_delay is not None else steps-shift_t,
        'adaptation_failed':adaptation_delay is None,
        'final_best_dist':statistics.mean(best_dist[-20:]),
        'pool_size':len(pool),
    }


def summarize(rows):
    out={}
    for mode in sorted(set(r['mode'] for r in rows)):
        s=[r for r in rows if r['mode']==mode]
        out[mode]={
            'n':len(s),
            'final_good_mean':statistics.mean(r['final_good'] for r in s),
            'adaptation_delay_median':statistics.median(r['adaptation_delay'] for r in s),
            'adaptation_failure_rate':statistics.mean(float(r['adaptation_failed']) for r in s),
            'generated_mean':statistics.mean(r['generated'] for r in s),
            'final_best_dist_mean':statistics.mean(r['final_best_dist'] for r in s),
            'pool_size_mean':statistics.mean(r['pool_size'] for r in s),
        }
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--seeds',type=int,default=1000); ap.add_argument('--json',action='store_true'); a=ap.parse_args()
    rows=[]
    for mode in ('fixed_no_generate','adaptive_no_generate','adaptive_generate'):
        for seed in range(a.seeds): rows.append(run(seed,mode))
    res={'schema':'adaptive-evolution.world-model-candidate-generation.v0.1','summary':summarize(rows)}
    print(json.dumps(res,indent=2,sort_keys=True) if a.json else res)
