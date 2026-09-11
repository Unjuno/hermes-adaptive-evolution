"""Portable R5 local hardening/release-gate control.
Requires --payload pointing to the cumulative tree after applying the R5 package.
No model/provider/billing call is performed.
"""
from __future__ import annotations
import argparse,hashlib,json,os,socket,struct,sys,tempfile,threading
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--payload',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise ValueError('refuse existing output')
 payload=a.payload.resolve();sys.path.insert(0,str(payload))
 from adaptive_evolution_observer.reviewed_worker_jail import prepare_reviewed_runtime,run_hardened_isolated_request,validate_reviewed_runtime
 from adaptive_evolution_observer.forced_mediation import SCHEMA
 from adaptive_evolution_observer.request_broker import REPLY_SCHEMA
 from adaptive_evolution_observer.release_gate import audit_release,POLICY_SCHEMA,EVIDENCE_SCHEMA
 from adaptive_evolution_observer.evidence_gate import digest
 from adaptive_evolution_observer.shadow_io import ShadowContractError
 from adaptive_evolution_observer.campaign_budget import PLAN_SCHEMA
 from adaptive_evolution_observer.request_broker import CONFIG_SCHEMA
 UID=GID=65534
 with tempfile.TemporaryDirectory(dir=str(payload.parent)) as td:
  root=Path(td);root.chmod(0o755);runtime=root/'runtime';contract=prepare_reviewed_runtime(runtime,authorized=True)
  # Content drift must be detected.
  target=runtime/'usr/lib/python3.13/json/__init__.py';target.write_bytes(target.read_bytes()+b'\n# drift-control\n');os.chmod(target,0o644)
  drift_rejected=False
  try:validate_reviewed_runtime(runtime)
  except ShadowContractError:drift_rejected=True
  # Prepare a fresh runtime for the actual fixed-client jail smoke.
  runtime2=root/'runtime2';prepare_reviewed_runtime(runtime2,authorized=True)
  ipc=root/'ipc';ipc.mkdir(mode=0o711);sp=ipc/'broker.sock'
  srv=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);srv.bind(str(sp));os.chown(sp,UID,GID);os.chmod(sp,0o600);srv.listen(1)
  def server():
   c,_=srv.accept();raw=c.recv(4);n=struct.unpack('!I',raw)[0];remaining=b''
   while len(remaining)<n:remaining+=c.recv(n-len(remaining))
   rep=json.dumps({'schema':REPLY_SCHEMA,'disposition':'DENIED','execution_authorized':False},sort_keys=True,separators=(',',':')).encode();c.sendall(struct.pack('!I',len(rep))+rep);c.close()
  th=threading.Thread(target=server,daemon=True);th.start()
  # Minimal structurally valid mediation config; fake broker only returns DENIED.
  now=1
  plan={'schema':'adaptive-evolution.local-text-pair-plan.v1','run_id':'r','endpoint':'http://127.0.0.1:9','provider_version':'v','model':'m','model_digest':'a'*64,'runtime_contract_hash':'b'*64,'max_calls':1,'max_total_tokens':100,'input_token_reserve':10,'output_token_limit':10,'socket_timeout_ms':100,'run_deadline_ms':1000,'attempts_per_task':1,'policies':{'candidate':'c','baseline':'b'},'tasks':[{'task_id':'t','prompt':'p','expected':1}]}
  camp={'schema':PLAN_SCHEMA,'campaign_id':'c','max_calls':1,'max_total_tokens':100,'runs':[{'run_id':'r','plan_hash':digest(plan),'max_calls':1,'max_total_tokens':100}]}
  bc={'schema':CONFIG_SCHEMA,'broker_id':'b','campaign':camp,'run_plans':[plan],'not_before_ns':1,'expires_at_ns':100000000,'clients':[{'client_id':'w','credential_sha256':'1'*64,'allowed_runs':['r']}]}
  mc={'schema':SCHEMA,'mediation_id':'m','broker_config':bc,'worker_uid':UID,'worker_gid':GID,'isolation_contract':{'network_namespace':'new_user_plus_net_namespace','separate_host_uid':True,'provider_route':'broker_only','socket_type':'filesystem_unix_stream'}}
  req={'schema':'adaptive-evolution.broker-request.v1','broker_hash':digest(bc),'client_id':'w','credential':'x','operation_id':'r:0:0:baseline'}
  jail=run_hardened_isolated_request(mc,sp,req,runtime2,authorized=True,timeout_s=3);th.join(timeout=2);srv.close()
  # Toy label-tamper release negative control.
  evidence_file=root/'local.json';evidence_file.write_text('{}')
  manifest={'schema':'adaptive-evolution.maturity-manifest.v0.1','manifest_id':'m','source_hash':'a'*64,'components':[{'component_id':'c','implementation_status':'tested_canary','value_status':'release_validated','authority_status':'none','dependencies':[],'blockers':[],'evidence_hashes':['b'*64]}]}
  policy={'schema':POLICY_SCHEMA,'release_id':'r','manifest_hash':digest(manifest),'requirements':[{'component_id':'c','min_implementation':'tested_canary','min_value':'real_canary','require_no_blockers':True,'evidence_kinds':['real_canary']}]}
  idx={'schema':EVIDENCE_SCHEMA,'index_id':'i','records':[{'evidence_id':'local','component_ids':['c'],'kind':'local_fixture','relative_path':'local.json','sha256':hashlib.sha256(evidence_file.read_bytes()).hexdigest()}]}
  release=audit_release(manifest,policy,idx,root)
  result={'schema':'hermes.r5-portable-local-control.v0.1','runtime_tree_entries':contract['tree_entries'],'runtime_drift_rejected':drift_rejected,'jail_disposition':jail['reply']['disposition'],'pid_namespace_init':jail['isolation']['pid_namespace_init'],'proc_absent':jail['isolation']['proc_absent'],'release_decision':release['decision'],'release_blockers':release['blockers'],'real_model':False,'execution_authorized':False}
  result['passed']=drift_rejected and result['jail_disposition']=='DENIED' and result['pid_namespace_init'] and result['proc_absent'] and release['decision']=='BLOCKED'
  result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
  if not result['passed']:raise SystemExit(2)
if __name__=='__main__':main()
