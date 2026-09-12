"""Portable R5 local acceptance reproducer.

Requires Linux root and --payload pointing to the cumulative implementation tree.
It performs only finite local process/canary checks. No model/provider call, billing,
or production authority is used.
"""
from __future__ import annotations
import argparse,hashlib,json,os,resource,subprocess,sys,tempfile,time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--payload',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    if a.output.exists():raise ValueError('refuse existing output')
    payload=a.payload.resolve();sys.path.insert(0,str(payload))
    from adaptive_evolution_observer.reviewed_canary import PLAN_SCHEMA,approval_hash,recover
    from adaptive_evolution_observer.evidence_gate import digest
    from adaptive_evolution_observer.shadow_io import ShadowContractError
    from adaptive_evolution_observer.forced_mediation import HARDENED_LIMITS
    if os.geteuid()!=0:raise RuntimeError('reviewed namespace reproducer requires root')
    # Finite resource/proc boundary probe.
    probe="""import ctypes,json,os,resource,subprocess\nout={}\nout['proc_count']=len(os.listdir('/proc'))\nout['nnp']=int(ctypes.CDLL(None).prctl(39,0,0,0,0))\nout['nproc']=list(resource.getrlimit(resource.RLIMIT_NPROC))\ncs=[]\nfor i in range(24):\n try:cs.append(subprocess.Popen(['/bin/sleep','0.08']))\n except OSError:break\nout['spawned']=len(cs)\nfor p in cs:p.wait()\nprint(json.dumps(out))"""
    lim=HARDENED_LIMITS
    shell='mount --make-rprivate /; mount -t tmpfs tmpfs /proc; exec "$@"'
    cmd=['setpriv','--reuid=65534','--regid=65534','--clear-groups','--no-new-privs','prlimit',
         f'--nproc={lim["nproc"]}:{lim["nproc"]}',f'--nofile={lim["nofile"]}:{lim["nofile"]}',
         f'--as={lim["as_bytes"]}:{lim["as_bytes"]}',f'--cpu={lim["cpu_seconds"]}:{lim["cpu_seconds"]}',
         f'--fsize={lim["fsize_bytes"]}:{lim["fsize_bytes"]}','--','unshare','--user','--map-root-user','--mount','--net','--pid','--fork','--','/bin/sh','-c',shell,'sh',sys.executable,'-I','-S','-B','-c',probe]
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=10,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin'},close_fds=True)
    boundary=json.loads(p.stdout) if p.returncode==0 else {'rc':p.returncode,'stderr':p.stderr}
    # Canary concurrent-state preservation check without arbitrary execution.
    TOK='a'*64
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/'r';root.mkdir(mode=0o700);(root/'state.json').write_text('{"template":"two_leaf"}\n')
        plan={'schema':PLAN_SCHEMA,'canary_id':'r5','from_state':{'template':'solo'},'to_state':{'template':'one_leaf'},'effect_class':'local_state_only_no_external_effects','expires_at_ns':time.time_ns()+10**9,'approval_sha256':approval_hash(TOK)}
        meta=root/'.canary';meta.mkdir(mode=0o700);(meta/'backup.json').write_text(json.dumps(plan['from_state'])+'\n')
        j={'schema':'adaptive-evolution.reviewed-canary-journal.v0.1','plan_hash':digest(plan),'phase':'APPLIED','before_hash':digest(plan['from_state']),'after_hash':digest(plan['to_state'])}
        (meta/'journal.json').write_text(json.dumps(j)+'\n')
        refused=False
        try:recover(root,plan)
        except ShadowContractError:refused=True
        preserved=json.loads((root/'state.json').read_text())=={'template':'two_leaf'}
    result={'schema':'hermes.r5-local-acceptance-reproduction.v1','boundary':boundary,
            'canary_unrelated_state_refused':refused,'canary_unrelated_state_preserved':preserved,
            'assertions':{'proc_masked':boundary.get('proc_count')==0,'no_new_privs':boundary.get('nnp')==1,
                          'process_cap_active':boundary.get('spawned',999)<24,'canary_preserves_third_state':refused and preserved},
            'real_model':False,'execution_authorized':False,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    result['all_pass']=all(result['assertions'].values())
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    if not result['all_pass']:raise SystemExit(2)
if __name__=='__main__':main()
