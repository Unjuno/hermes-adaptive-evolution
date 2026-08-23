from __future__ import annotations

import argparse, json, math
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Tuple
import numpy as np

TOOL_TYPES = ("read", "write", "delete", "transfer")
POLICIES = (
    "actor_self_report",
    "noisy_external",
    "typed_stale_continue",
    "typed_failclosed",
    "typed_degraded",
)

@dataclass(frozen=True)
class Meta:
    version: int
    write_max: float
    transfer_max: float
    allow_delete: bool

META_V1 = Meta(1, 0.22, 0.22, True)
META_V2 = Meta(2, 0.12, 0.10, False)
COARSE = Meta(-1, 0.08, 0.06, False)

@dataclass(frozen=True)
class Scenario:
    name: str
    manipulation_p: float = 0.0
    shift_t: int = -1
    root_outage_start: int = -1
    root_outage_len: int = 0
    domain_start_p: float = 0.01
    domain_mean_len: float = 4.0
    fallback_independent_fail_p: float = 0.01
    fallback_common_p: float = 0.04
    noisy_gate_fn_p: float = 0.08
    noisy_gate_fp_p: float = 0.05

SCENARIOS = (
    Scenario("clean"),
    Scenario("manipulation", manipulation_p=0.25),
    Scenario("drift_stale", manipulation_p=0.08, shift_t=180),
    Scenario("root_outage", manipulation_p=0.08, shift_t=180, root_outage_start=180, root_outage_len=60),
    Scenario("combined", manipulation_p=0.25, shift_t=180, root_outage_start=180, root_outage_len=60,
             domain_start_p=0.025, domain_mean_len=6.0, fallback_independent_fail_p=0.03, fallback_common_p=0.18),
)

@dataclass
class Call:
    tool: str
    args: Dict[str, Any]
    claimed_utility: float
    claimed_confidence: float
    claimed_safe: bool
    task_value: float


def true_meta(t:int, sc:Scenario)->Meta:
    return META_V2 if sc.shift_t >= 0 and t >= sc.shift_t else META_V1


def root_available(t:int, sc:Scenario)->bool:
    if sc.root_outage_start < 0: return True
    return not (sc.root_outage_start <= t < sc.root_outage_start + sc.root_outage_len)


def certified(call:Call, meta:Meta, balances:np.ndarray)->bool:
    a=call.args
    if call.tool == "read":
        return a["namespace"] == "public"
    if call.tool == "write":
        return (not a["protected"]) and abs(float(a["delta"])) <= meta.write_max + 1e-12
    if call.tool == "delete":
        return meta.allow_delete and (not a["protected"])
    if call.tool == "transfer":
        amt=float(a["amount"]); src=int(a["src"])
        return amt <= meta.transfer_max + 1e-12 and amt <= balances[src] + 1e-12 and amt >= 0
    raise ValueError(call.tool)


def generate_selected_call(rng:np.random.Generator, t:int, sc:Scenario, balances:np.ndarray)->Call:
    tool=TOOL_TYPES[int(rng.integers(0,len(TOOL_TYPES)))]
    val=float(rng.uniform(0.75,1.25))
    manipulated=bool(rng.random() < sc.manipulation_p)
    # Actor intentionally remains on v1 assumptions after drift; external safety owns freshness.
    if tool=="read":
        risky=manipulated or rng.random()<0.003
        ns="private" if risky else "public"
        claim=val + (0.45 if risky and manipulated else -0.06 if risky else 0.05) + rng.normal(0,.04)
        return Call(tool,{"namespace":ns,"key":int(rng.integers(0,8))},claim,float(np.clip(.84+rng.normal(0,.08),0,1)),(True if manipulated else (not risky)),val)
    if tool=="write":
        desired=float(rng.uniform(.04,.20)); protected=bool(rng.random()<(.22 if manipulated else .003))
        if manipulated: desired=min(.32,desired*float(rng.uniform(1.2,1.8)))
        risky=protected or desired > META_V1.write_max
        claim=val + (.42 if manipulated and (protected or desired>.12) else .03) + rng.normal(0,.05)
        # claimed_safe uses stale V1 and ignores current v2.
        claimed=True if manipulated else ((not protected) and desired<=META_V1.write_max)
        return Call(tool,{"key":int(rng.integers(0,12)),"protected":protected,"delta":desired},claim,float(np.clip(.87+rng.normal(0,.07),0,1)),claimed,val)
    if tool=="delete":
        protected=bool(rng.random()<(.35 if manipulated else .003))
        claim=val + (.5 if manipulated else .01) + rng.normal(0,.05)
        claimed=True if manipulated else (not protected)  # manipulation can falsely self-attest; otherwise stale V1 permits unprotected delete after v2.
        return Call(tool,{"key":int(rng.integers(0,12)),"protected":protected},claim,float(np.clip(.9+rng.normal(0,.06),0,1)),claimed,val)
    # transfer
    src=int(rng.integers(0,4)); dst=(src+int(rng.integers(1,4)))%4
    affordable=max(.005,min(.20,float(balances[src])*.80))
    desired=float(rng.uniform(.005,affordable))
    if manipulated: desired=min(.35,max(desired, .04)*float(rng.uniform(1.3,2.0)))
    claim=val + (.48 if manipulated and (desired>.10 or desired>balances[src]) else .02) + rng.normal(0,.05)
    claimed=True if manipulated else (desired<=META_V1.transfer_max and desired<=balances[src])
    return Call(tool,{"src":src,"dst":dst,"amount":desired},claim,float(np.clip(.88+rng.normal(0,.07),0,1)),claimed,val)


def safe_fallback(call:Call, meta:Meta, balances:np.ndarray)->Call|None:
    # Prefer a cross-domain, lower-impact operation when possible.
    v=call.task_value
    if call.tool=="read":
        return Call("read",{"namespace":"public","key":0},.35,.99,True,v*.55)
    if call.tool=="write":
        return Call("read",{"namespace":"public","key":int(call.args["key"])},.35,.99,True,v*.52)
    if call.tool=="delete":
        return Call("write",{"key":int(call.args["key"]),"protected":False,"delta":min(.04,meta.write_max)},.35,.99,True,v*.58)
    if call.tool=="transfer":
        # Queue/record intent rather than move resource.
        return Call("write",{"key":99,"protected":False,"delta":min(.03,meta.write_max)},.35,.99,True,v*.50)
    return None


def tool_domain(tool:str)->int:
    return {"read":0,"write":1,"delete":1,"transfer":2}[tool]


def build_faults(rng:np.random.Generator, steps:int, sc:Scenario):
    down=np.zeros((steps,3),dtype=bool); remain=np.zeros(3,dtype=int)
    for t in range(steps):
        for d in range(3):
            if remain[d]>0:
                down[t,d]=True; remain[d]-=1
            elif rng.random()<sc.domain_start_p:
                dur=max(1,int(rng.geometric(1.0/sc.domain_mean_len)))
                down[t,d]=True; remain[d]=dur-1
    return {
        "domain_down":down,
        "fallback_u":rng.random(steps),
        "common_u":rng.random(steps),
        "noisy_fn_u":rng.random(steps),
        "noisy_fp_u":rng.random(steps),
    }


def execute(call:Call|None, meta_true:Meta, balances:np.ndarray, mode:str)->Tuple[float,bool,bool]:
    """return true utility, task success, invariant violation"""
    if call is None:
        return 0.08, False, False
    ok=certified(call,meta_true,balances)
    if not ok:
        # Unsafe calls can look locally attractive but are poor downstream outcomes.
        return -0.85*call.task_value, False, True
    if call.tool=="transfer":
        a=call.args; amt=float(a["amount"]); src=int(a["src"]); dst=int(a["dst"])
        balances[src]-=amt; balances[dst]+=amt
    if mode=="primary": return call.task_value, True, False
    if mode=="fallback": return 0.68*call.task_value, True, False
    return 0.08, False, False


def run(seed:int, sc:Scenario, policy:str, steps:int=360)->dict:
    rng=np.random.default_rng(50_000+seed)
    faults=build_faults(np.random.default_rng(90_000+seed),steps,sc)
    balances=np.full(4,.55,float)
    cached=META_V1
    protected_version=1
    mode="NORMAL"
    last_refresh_attempt=-999
    root_calls=0

    us=[]; succ=[]; leaks=[]; false_blocks=[]; blocks=[]; fbs=[]; fbf=[]; holds=[]; susp=[]; degraded=[]; failclosed=[]; claims=[]
    pertool={z:{'n':0,'success':0,'leak':0,'block':0} for z in TOOL_TYPES}

    for t in range(steps):
        tm=true_meta(t,sc)
        if tm.version>protected_version:
            protected_version=tm.version  # protected monotonic version bulletin.
        call=generate_selected_call(rng,t,sc,balances)
        true_safe=certified(call,tm,balances)
        claims.append(bool(call.claimed_safe and not true_safe))
        selected:Call|None=call
        blocked=False; used_fb=False; fb_failed=False; held=False; suspended=False
        cost=0.0

        # Metadata refresh state for typed policies.
        if policy.startswith("typed_") and cached.version != protected_version:
            if policy=="typed_stale_continue":
                mode="STALE"
            else:
                if t-last_refresh_attempt>=8 or root_available(t,sc):
                    last_refresh_attempt=t; root_calls+=1; cost+=.006
                    if root_available(t,sc):
                        cached=tm; mode="NORMAL"
                    else:
                        mode="DEGRADED" if policy=="typed_degraded" else "FAIL_CLOSED"
                else:
                    mode="DEGRADED" if policy=="typed_degraded" else "FAIL_CLOSED"

        if policy=="actor_self_report":
            allowed=call.claimed_safe and call.claimed_confidence>=.55
        elif policy=="noisy_external":
            # Noisy external risk model observes the same structured call but is statistical, not a hard certifier.
            unsafe=not true_safe
            if unsafe:
                allowed=bool(faults["noisy_fn_u"][t] < sc.noisy_gate_fn_p)  # false negative allows
            else:
                allowed=not bool(faults["noisy_fp_u"][t] < sc.noisy_gate_fp_p)
        elif policy.startswith("typed_"):
            if mode=="FAIL_CLOSED" and call.tool!="read":
                allowed=False
            else:
                gate_meta = COARSE if mode=="DEGRADED" else cached
                allowed=certified(call,gate_meta,balances)
        else: raise ValueError(policy)

        if not allowed:
            blocked=True
            false_blocks.append(bool(true_safe))
            gate_meta = COARSE if (policy=="typed_degraded" and mode=="DEGRADED") else (cached if policy.startswith("typed_") else tm)
            # Statistical gates and actor-only do not have certified fallback machinery.
            if policy in ("actor_self_report","noisy_external"):
                selected=None; held=True
            else:
                fb=safe_fallback(call,gate_meta,balances)
                if mode=="FAIL_CLOSED" and fb is not None and fb.tool!="read":
                    fb=None
                if fb is not None and certified(fb,gate_meta,balances):
                    used_fb=True
                    pd=tool_domain(call.tool); fd=tool_domain(fb.tool)
                    operational = (not faults["domain_down"][t,fd]) and not (
                        fd==pd and faults["common_u"][t] < sc.fallback_common_p
                    ) and faults["fallback_u"][t]>=sc.fallback_independent_fail_p
                    if operational:
                        selected=fb
                    else:
                        fb_failed=True; selected=None; held=True
                else:
                    selected=None; held=True
        else:
            false_blocks.append(False)

        # Typed architecture terminal suspension: if fallback/hold path is needed, no original unsafe call can re-enter.
        if held and policy.startswith("typed_"):
            suspended=True; selected=None

        emode="primary"
        if used_fb and selected is not None: emode="fallback"
        elif selected is None: emode="hold"
        u,success,leak=execute(selected,tm,balances,emode)
        u-=cost
        z=call.tool; pertool[z]['n']+=1; pertool[z]['success']+=int(success); pertool[z]['leak']+=int(leak); pertool[z]['block']+=int(blocked)
        us.append(u);succ.append(success);leaks.append(leak);blocks.append(blocked);fbs.append(used_fb);fbf.append(fb_failed);holds.append(held);susp.append(suspended)
        degraded.append(mode=="DEGRADED");failclosed.append(mode=="FAIL_CLOSED")

    return {
        "seed":seed,"scenario":sc.name,"policy":policy,
        "mean_utility":float(np.mean(us)),"task_success_rate":float(np.mean(succ)),
        "uncertified_leak_rate":float(np.mean(leaks)),"any_invariant_violation":bool(np.any(leaks)),
        "false_block_rate":float(np.mean(false_blocks)),"block_rate":float(np.mean(blocks)),
        "fallback_rate":float(np.mean(fbs)),"fallback_failure_rate":float(np.mean(fbf)),
        "hold_rate":float(np.mean(holds)),"suspension_rate":float(np.mean(susp)),
        "root_call_rate":float(root_calls/steps),"degraded_rate":float(np.mean(degraded)),"failclosed_rate":float(np.mean(failclosed)),
        "unsafe_claimed_safe_rate":float(np.mean(claims)),
        "tool_breakdown":{z:{"n":v["n"],"success_rate":v["success"]/max(1,v["n"]),"leak_rate":v["leak"]/max(1,v["n"]),"block_rate":v["block"]/max(1,v["n"])} for z,v in pertool.items()},
    }


def ci(vals:List[float]):
    x=np.asarray(vals,float); m=float(x.mean()); se=float(x.std(ddof=1)/math.sqrt(len(x))) if len(x)>1 else 0
    return [m,m-1.96*se,m+1.96*se]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--seeds",type=int,default=64); ap.add_argument("--scenario",default="all"); ap.add_argument("--out",required=True)
    a=ap.parse_args()
    scenarios=SCENARIOS if a.scenario=="all" else tuple(s for s in SCENARIOS if s.name==a.scenario)
    rows=[]
    for si,sc in enumerate(scenarios):
        base=250000+si*10000
        for i in range(a.seeds):
            seed=base+i
            for p in POLICIES: rows.append(run(seed,sc,p))
    summary={}
    metrics=["mean_utility","task_success_rate","uncertified_leak_rate","any_invariant_violation","false_block_rate","block_rate","fallback_rate","fallback_failure_rate","hold_rate","suspension_rate","root_call_rate","degraded_rate","failclosed_rate","unsafe_claimed_safe_rate"]
    for sc in scenarios:
        summary[sc.name]={}
        for p in POLICIES:
            ss=[r for r in rows if r["scenario"]==sc.name and r["policy"]==p]
            summary[sc.name][p]={k:float(np.mean([float(r[k]) for r in ss])) for k in metrics}
        # Paired typed-degraded vs key controls.
        summary[sc.name]["paired"]={}
        for q in ("actor_self_report","noisy_external","typed_stale_continue","typed_failclosed"):
            ds={k:[] for k in ("mean_utility","task_success_rate","uncertified_leak_rate","any_invariant_violation","false_block_rate")}
            for i in range(a.seeds):
                seed=250000+list(scenarios).index(sc)*10000+i
                x=next(r for r in rows if r["scenario"]==sc.name and r["seed"]==seed and r["policy"]=="typed_degraded")
                y=next(r for r in rows if r["scenario"]==sc.name and r["seed"]==seed and r["policy"]==q)
                for k in ds: ds[k].append(float(x[k])-float(y[k]))
            summary[sc.name]["paired"]["typed_degraded-vs-"+q]={k:ci(v) for k,v in ds.items()}
    out={"schema":"adaptive-evolution.typed-tool-transfer.v0.1","seeds":a.seeds,"scenarios":[asdict(x) for x in scenarios],"summary":summary,"rows":rows}
    with open(a.out,"w") as f: json.dump(out,f,indent=2)
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
