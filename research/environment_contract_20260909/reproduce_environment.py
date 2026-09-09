"""Reviewed finite state-carryover controls; NOT Hermes, an LLM, or a sandbox.
All mutable paths live below the temporary study directory. No provider calls.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, signal, subprocess, sys, tempfile, time
from pathlib import Path

FIXTURES = {
 'clamp': ('def solve(x, lo, hi):\n return min(max(x, lo), hi-1)\n',
           'def solve(x, lo, hi):\n return min(max(x, lo), hi)\n', [([8,0,3],3),([-2,0,3],0),([3,0,3],3)]),
 'unique': ('def solve(x):\n return list(x)\n', 'def solve(x):\n return list(dict.fromkeys(x))\n', [([[2,1,2]],[2,1]),([[]],[]),([[3,3,1]],[3,1])]),
 'total': ('def solve(x):\n return sum(x[:-1])\n', 'def solve(x):\n return sum(x)\n', [([[1,2,3]],6),([[]],0),([[7]],7)])}
SURFACES={'home':'HOME','profile':'HERMES_HOME','cache':'XDG_CACHE_HOME','external_surrogate':'REVIEWED_SHARED_STORE'}
def sha(b): return hashlib.sha256(b).hexdigest()
def env_for(root):
    env={'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    for key,name in [('HOME','home'),('HERMES_HOME','profile'),('XDG_CACHE_HOME','cache'),('TMPDIR','tmp')]:
        p=root/name;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
    return env

def invoke(args,cwd,env):
    start=time.monotonic_ns()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),*args],cwd=cwd,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
        timeout=False
        try:p.wait(timeout=2)
        except subprocess.TimeoutExpired:timeout=True
        finally:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait(timeout=2)
        out.seek(0);err.seek(0);raw=out.read(8192).decode();error=err.read(4096).decode()
    try:receipt=json.loads(raw)
    except (ValueError,TypeError):receipt=None
    return {'exit':p.returncode,'timeout':timeout,'receipt':receipt,'stderr':error,'wall_ns':time.monotonic_ns()-start}

def child(mode,fixture,surface):
    buggy,fixed,cases=FIXTURES[fixture]
    if mode=='verify':
        spec=importlib.util.spec_from_file_location('reviewed_solution',Path.cwd()/'solution.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        results=[mod.solve(*a)==b for a,b in cases]
        print(json.dumps({'schema':'reviewed.environment.verification.v1','completed':True,'cases':len(cases),'score':int(all(results))}));return
    path=Path(os.environ[SURFACES[surface]])/('fixture-'+fixture+'.json')
    # A reviewed memory-assisted baseline, NOT a claim about Hermes memory tools.
    hit=path.is_file() and json.loads(path.read_text())=={'learned_repair':fixture,'version':1}
    if mode=='candidate' or hit:Path('solution.py').write_text(fixed)
    if mode=='candidate':
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'learned_repair':fixture,'version':1}))
    print(json.dumps({'schema':'reviewed.environment.worker.v1','memory_hit':hit,'arm':mode}))

def one(surface,scope,order,fixture,attempt):
    with tempfile.TemporaryDirectory(prefix='reviewed-state-study-') as tmp:
        root=Path(tmp);shared=root/'shared';shared.mkdir();rows={}
        for arm in order:
            work=root/(arm+'-work');work.mkdir();(work/'solution.py').write_text(FIXTURES[fixture][0])
            initial=sha((work/'solution.py').read_bytes())
            env=env_for(root/arm)
            if scope=='shared' or surface=='external_surrogate':env[SURFACES[surface]]=str(shared)
            worker=invoke(['--worker',arm,'--fixture',fixture,'--surface',surface],work,env)
            # The verifier never reads the mutable memory used by the two policies.
            verification=invoke(['--worker','verify','--fixture',fixture,'--surface',surface],work,env_for(root/(arm+'-verifier')))
            v=verification['receipt'];known=verification['exit']==0 and not verification['timeout'] and isinstance(v,dict) and v.get('completed') is True
            score=v['score'] if known and worker['exit']==0 and not worker['timeout'] else None
            rows[arm]={'input_hash':initial,'worker':worker,'verification':verification,'score':score}
        return {'surface':surface,'scope':scope,'order':list(order),'fixture':fixture,'attempt':attempt,'arms':rows,
                'equal_pristine_worktrees':rows['candidate']['input_hash']==rows['baseline']['input_hash'],
                'raw_delta':None if any(r['score'] is None for r in rows.values()) else rows['candidate']['score']-rows['baseline']['score']}

def study(repeats,followup=False,cell_index=None):
    surfaces=['external_surrogate'] if followup else ['home','profile','cache']
    scopes=['private_local_roots'] if followup else ['shared','private']
    rows=[];cell=-1
    for surface in surfaces:
      for scope in scopes:
       for order in [('baseline','candidate'),('candidate','baseline')]:
        cell+=1
        if cell_index is not None and cell != cell_index:continue
        for fixture in FIXTURES:
         for attempt in range(repeats):rows.append(one(surface,scope,order,fixture,attempt))
    cells=[]
    for surface in surfaces:
     for scope in scopes:
      for order in [('baseline','candidate'),('candidate','baseline')]:
       rr=[r for r in rows if r['surface']==surface and r['scope']==scope and r['order']==list(order)]
       if not rr:continue
       vals=[r['raw_delta'] for r in rr if r['raw_delta'] is not None]
       cells.append({'surface':surface,'scope':scope,'order':list(order),'pairs':len(rr),'unknown_pairs':len(rr)-len(vals),
                     'mean_raw_delta':None if not vals else sum(vals)/len(vals),
                     'baseline_memory_hits':sum(bool((r['arms']['baseline']['worker']['receipt'] or {}).get('memory_hit')) for r in rr)})
    return {'schema':'hermes.reviewed-environment-study.v1','date':'2026-09-09','followup':followup,'repeats':repeats,'source_sha256':sha(Path(__file__).read_bytes()),'cells':cells,'rows':rows,
            'no_network_or_provider_calls':True,'hermes_or_llm_executed':False,'population_inference':False,'execution_authorized':False,
            'scope':'Reviewed memory-assisted baseline and fixed repair policy; shared service is a local surrogate, not an actual provider'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worker',choices=['candidate','baseline','verify']);ap.add_argument('--fixture',choices=list(FIXTURES));ap.add_argument('--surface',choices=list(SURFACES));ap.add_argument('--followup',action='store_true');ap.add_argument('--cell-index',type=int);ap.add_argument('--repeats',type=int,default=4);ap.add_argument('--output',type=Path);a=ap.parse_args()
    if a.worker:child(a.worker,a.fixture,a.surface);return
    if not a.output or a.output.exists() or not 1<=a.repeats<=8:raise SystemExit('new output and repeats 1..8 required')
    a.output.parent.mkdir(parents=True,exist_ok=True);res=study(a.repeats,a.followup,a.cell_index)
    with a.output.open('x') as f:json.dump(res,f,indent=2)
    print(json.dumps(res['cells'],indent=2))
if __name__=='__main__':main()
