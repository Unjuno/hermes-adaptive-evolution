from __future__ import annotations
import hashlib, json, random
from dataclasses import dataclass

SEED=20260828
N=60000
rng=random.Random(SEED)

RESERVED={
 'role':'proposer_only',
 'authority':'runtime_only',
 'source_intent':'immutable',
 'retry':'no_semantic_bypass',
 'fallback':'same_semantic_guard',
 'learning_credit':'committed_effect',
 'prompt_core':'immutable',
}
ALLOWED_DYNAMIC={'task_patch','context_belief','specialist_annotation','runtime_feedback','memory_evidence'}

@dataclass(frozen=True)
class Patch:
    kind:str
    key:str
    value:str
    patch_id:str

core_blob=json.dumps(RESERVED,sort_keys=True,separators=(',',':')).encode()
CORE_HASH=hashlib.sha256(core_blob).hexdigest()

def naive_concat(patches):
    state=dict(RESERVED)
    for p in patches: state[p.key]=p.value
    return state

def strict_assemble(patches):
    dynamic=[]
    rejects=[]
    for p in patches:
        if p.key in RESERVED:
            rejects.append((p.patch_id,'reserved_key_override'))
            continue
        if p.kind not in ALLOWED_DYNAMIC:
            rejects.append((p.patch_id,'unknown_patch_kind'))
            continue
        dynamic.append((p.patch_id,p.kind,p.key,p.value))
    state={'core':dict(RESERVED),'core_hash':CORE_HASH,'dynamic':dynamic}
    assert hashlib.sha256(json.dumps(state['core'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==CORE_HASH
    return state,rejects

def make_case(i):
    attack=rng.random()<.36
    patches=[]
    normal_n=rng.randint(1,5)
    for j in range(normal_n):
        kind=rng.choice(tuple(ALLOWED_DYNAMIC))
        patches.append(Patch(kind,f'note_{i}_{j}',f'value_{rng.randint(0,999)}',f'p{i}_{j}'))
    family='normal'
    if attack:
        fam=rng.choice(('authority_override','retry_bypass','core_rewrite','credit_rebind','unknown_kind'))
        family=fam
        if fam=='authority_override': patches.append(Patch('task_patch','authority','agent_may_override',f'a{i}'))
        elif fam=='retry_bypass': patches.append(Patch('runtime_feedback','retry','retry_until_pass',f'a{i}'))
        elif fam=='core_rewrite': patches.append(Patch('task_patch','prompt_core','replace_core',f'a{i}'))
        elif fam=='credit_rebind': patches.append(Patch('memory_evidence','learning_credit','proposal_identity',f'a{i}'))
        elif fam=='unknown_kind': patches.append(Patch('system_override',f'opaque_{i}','bypass',f'a{i}'))
    rng.shuffle(patches)
    return family,patches

naive_core_override=0; strict_core_override=0; strict_attack_reject=0; strict_normal_reject=0
families={}
for i in range(N):
    fam,patches=make_case(i); families[fam]=families.get(fam,0)+1
    naive=naive_concat(patches)
    if any(naive.get(k)!=v for k,v in RESERVED.items()): naive_core_override+=1
    strict,rejects=strict_assemble(patches)
    if strict['core']!=RESERVED: strict_core_override+=1
    if fam!='normal' and rejects: strict_attack_reject+=1
    if fam=='normal' and rejects: strict_normal_reject+=1

res={
 'schema':'humies.agent-prompt-supply-chain-integrity.v0.1',
 'config':{'seed':SEED,'cases':N,'attack_probability':.36,'core_hash':CORE_HASH},
 'families':families,
 'summary':{
  'naive_core_override_rate':naive_core_override/N,
  'strict_core_override_rate':strict_core_override/N,
  'strict_attack_reject_rate':strict_attack_reject/max(1,N-families.get('normal',0)),
  'strict_normal_false_reject_rate':strict_normal_reject/max(1,families.get('normal',0)),
 }
}
print(json.dumps(res,indent=2,sort_keys=True))
