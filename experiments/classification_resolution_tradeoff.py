from __future__ import annotations
import argparse, json, math, random, statistics

INFO_TYPES = 4
N_AGENTS = 48
STEPS = 260
SHIFT_T = 130
MESSAGES_PER_STEP = 20
RECIPIENTS = 3


def clip(x): return max(0.0, min(1.0, x))


def make_capabilities(rng):
    caps=[]
    for _ in range(N_AGENTS):
        base=[rng.betavariate(2.2,2.2) for _ in range(INFO_TYPES)]
        caps.append(base)
    return caps


def shift_capabilities(caps, rng):
    out=[]
    for c in caps:
        shifted=c[1:]+c[:1]
        out.append([clip(0.8*x + 0.2*rng.random()) for x in shifted])
    return out


def role_labels(caps):
    return [max(range(INFO_TYPES), key=lambda j:c[j]) for c in caps]


def message_type(rng):
    return rng.randrange(INFO_TYPES)


def outcome_prob(cap, info_type, context_noise, sender_quality):
    z = 0.68*cap[info_type] + 0.18*sender_quality + 0.14*(1-context_noise)
    return clip(z)


def run(seed, mode, memory_half_life=60.0):
    rng=random.Random(seed)
    caps0=make_capabilities(rng)
    caps1=shift_capabilities(caps0,rng)
    labels=role_labels(caps0)

    cap_est=[[0.5]*INFO_TYPES for _ in range(N_AGENTS)]
    cap_weight=[[0.0]*INFO_TYPES for _ in range(N_AGENTS)]
    inter_est=[[[0.5]*INFO_TYPES for _ in range(N_AGENTS)] for __ in range(INFO_TYPES)]
    inter_weight=[[[0.0]*INFO_TYPES for _ in range(N_AGENTS)] for __ in range(INFO_TYPES)]

    total_utility=0.0; total_harm=0; nrecv=0; updates=0
    pre=[]; post=[]

    if mode=='role': memory_slots=N_AGENTS
    elif mode=='capability': memory_slots=N_AGENTS*INFO_TYPES
    elif mode=='interaction': memory_slots=N_AGENTS*INFO_TYPES*INFO_TYPES
    elif mode=='random': memory_slots=0
    else: raise ValueError(mode)

    decay=0.5**(1.0/memory_half_life)

    for t in range(STEPS):
        caps=caps0 if t<SHIFT_T else caps1
        for i in range(N_AGENTS):
            for k in range(INFO_TYPES):
                cap_weight[i][k]*=decay
            if mode=='interaction':
                for st in range(INFO_TYPES):
                    for k in range(INFO_TYPES):
                        inter_weight[st][i][k]*=decay

        step_util=[]
        for _ in range(MESSAGES_PER_STEP):
            sender=rng.randrange(N_AGENTS)
            it=message_type(rng)
            sender_type=labels[sender]
            sender_quality=0.5+0.5*caps[sender][it]
            context_noise=rng.random()*0.35

            candidates=[i for i in range(N_AGENTS) if i!=sender]
            if mode=='random':
                chosen=rng.sample(candidates, RECIPIENTS)
            elif mode=='role':
                same=[i for i in candidates if labels[i]==it]
                pool=same if len(same)>=RECIPIENTS else candidates
                chosen=sorted(pool, key=lambda i:(labels[i]==it, rng.random()), reverse=True)[:RECIPIENTS]
            elif mode=='capability':
                chosen=sorted(candidates,key=lambda i:cap_est[i][it], reverse=True)[:RECIPIENTS]
            else:
                chosen=sorted(candidates,key=lambda i:inter_est[sender_type][i][it], reverse=True)[:RECIPIENTS]

            for r in chosen:
                p=outcome_prob(caps[r],it,context_noise,sender_quality)
                ok=rng.random()<p
                util=(1.0 if ok else -0.65)
                total_utility+=util; total_harm+=int(not ok); nrecv+=1; step_util.append(util)

                if mode in ('capability','interaction'):
                    w=cap_weight[r][it]
                    alpha=1.0/(1.0+w)
                    cap_est[r][it]=(1-alpha)*cap_est[r][it]+alpha*(1.0 if ok else 0.0)
                    cap_weight[r][it]+=1.0; updates+=1
                if mode=='interaction':
                    w=inter_weight[sender_type][r][it]
                    alpha=1.0/(1.0+w)
                    inter_est[sender_type][r][it]=(1-alpha)*inter_est[sender_type][r][it]+alpha*(1.0 if ok else 0.0)
                    inter_weight[sender_type][r][it]+=1.0; updates+=1

        avg=statistics.mean(step_util)
        (pre if t<SHIFT_T else post).append(avg)

    storage_cost=memory_slots/(N_AGENTS*INFO_TYPES*INFO_TYPES)
    update_cost=updates/(STEPS*MESSAGES_PER_STEP*RECIPIENTS*2)
    utility_per_recv=total_utility/nrecv
    harmful_rate=total_harm/nrecv
    net=utility_per_recv - 0.06*storage_cost - 0.04*update_cost
    return {
      'mode':mode,'utility':utility_per_recv,'harmful_rate':harmful_rate,
      'pre_utility':statistics.mean(pre),'post_utility':statistics.mean(post),
      'storage_cost':storage_cost,'update_cost':update_cost,'net_utility':net,
    }


def summarize(rows):
    out={}
    for mode in sorted(set(r['mode'] for r in rows)):
        sub=[r for r in rows if r['mode']==mode]
        out[mode]={k:statistics.mean(r[k] for r in sub) for k in ['utility','harmful_rate','pre_utility','post_utility','storage_cost','update_cost','net_utility']}
        out[mode]['n']=len(sub)
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seeds',type=int,default=500); ap.add_argument('--json',action='store_true')
    a=ap.parse_args(); rows=[]
    for mode in ['random','role','capability','interaction']:
        for seed in range(a.seeds): rows.append(run(seed,mode))
    result={'schema':'adaptive-evolution.classification-resolution.v0.1','seeds':a.seeds,'summary':summarize(rows)}
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
