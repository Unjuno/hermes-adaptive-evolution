from __future__ import annotations

import itertools, math, random, statistics


def simulate(seed:int, speed:str, target:str, representation:str, receiver:str, steps:int=160, n_agents:int=36):
    rng=random.Random(seed)
    roles=[i%3 for i in range(n_agents)]  # 0 executor, 1 verifier, 2 archive
    belief=[0.0]*n_agents
    shift=steps//2
    truth=lambda t: 1 if t<shift else -1
    horizon=[1,3,1,5,12,30]  # action,state,warning,verification,pattern,abstract
    best=[{0},{0,1},{0,1},{1,2},{0,2},{2}]
    err=[.08,.10,.06,.04,.18,.20]
    fidelity={
        'raw':[.95,.95,.95,.95,.80,.65],
        'compressed':[.90,.88,.90,.88,.90,.82],
        'abstract':[.65,.70,.70,.78,.92,.96],
    }[representation]
    latmean=.5 if speed=='fast' else 3.5
    pending=[]; correct=opp=useful=harmful=sent=0; arch_s=arch_w=0.0
    for t in range(steps):
        nxt=[]
        for created,due,r,typ,sig in pending:
            if due>t:
                nxt.append((created,due,r,typ,sig)); continue
            age=t-created; timely=math.exp(-age/horizon[typ]); aligned=roles[r] in best[typ]
            accept=.9 if receiver=='local' else (.94 if aligned else .62)
            if rng.random()>accept: continue
            stale=(truth(created)!=truth(t) and typ in (0,1,4,5))
            eff=fidelity[typ]*timely*(1 if aligned else .55)
            if receiver=='context' and stale: eff*=.35
            semantic=(sig==truth(t))
            if typ==5 and roles[r]==2:
                arch_s+=eff*sig; arch_w+=eff
            else:
                belief[r]+=eff*sig
            useful += int(semantic and aligned and timely>.5)
            harmful += int((not semantic) or ((not aligned) and eff>.25))
        pending=nxt
        for _ in range(4):
            typ=rng.randrange(6); sig=truth(t) if rng.random()>err[typ] else -truth(t)
            if target=='broadcast': pool=list(range(n_agents))
            elif target=='targeted': pool=[i for i in range(n_agents) if roles[i] in best[typ]]
            else: pool=[i for i in range(n_agents) if roles[i] in best[typ]] if rng.random()<.75 else list(range(n_agents))
            # Equal message budget across routing policies.
            for r in rng.sample(pool,3):
                sent+=1; lat=int(rng.expovariate(1/latmean))
                sig2=truth(t) if (speed=='slow' and typ in (3,4,5) and rng.random()<.08) else sig
                pending.append((t,t+lat,r,typ,sig2))
        prior=arch_s/arch_w if arch_w else 0
        for i in range(n_agents):
            if roles[i]!=0: continue
            opp+=1; score=belief[i]+((.35 if receiver=='context' else .15)*prior)
            correct += ((1 if score>=0 else -1)==truth(t))
            belief[i]*=.92 if receiver=='context' else .96
        arch_s*=.995; arch_w*=.995
    return correct/opp, useful/sent, harmful/sent


def channel_value(seed:int, info_type:str, speed:str, n:int=1000):
    rng=random.Random(seed)
    horizon={'action':1,'warning':1,'verification':8,'pattern':15,'abstract':30}[info_type]
    base_err={'action':.08,'warning':.06,'verification':.18,'pattern':.22,'abstract':.28}[info_type]
    correction={'action':.01,'warning':.01,'verification':.13,'pattern':.15,'abstract':.20}[info_type] if speed=='slow' else 0
    latmean=.5 if speed=='fast' else 3.5
    value=0.0
    for _ in range(n):
        correct=rng.random()>base_err
        if not correct and rng.random()<correction: correct=True
        latency=rng.expovariate(1/latmean)
        timely=math.exp(-latency/horizon)
        value += (1 if correct else -1.2)*timely
    return value/n


def main():
    conditions=list(itertools.product(['fast','slow'],['broadcast','targeted','mixed'],['raw','compressed','abstract'],['local','context']))
    rows=[]
    for cond in conditions:
        vals=[simulate(seed,*cond) for seed in range(80)]
        rows.append((cond,)*(1) + tuple(statistics.mean(v[i] for v in vals) for i in range(3)))
    print('FACTORIAL')
    for r in sorted(rows,key=lambda x:x[1],reverse=True)[:10]: print(r)
    print('CHANNEL_CROSSOVER')
    for typ in ['action','warning','verification','pattern','abstract']:
        fast=statistics.mean(channel_value(s,typ,'fast') for s in range(100))
        slow=statistics.mean(channel_value(s,typ,'slow') for s in range(100))
        print(typ, {'fast':fast,'slow':slow})

if __name__=='__main__': main()
