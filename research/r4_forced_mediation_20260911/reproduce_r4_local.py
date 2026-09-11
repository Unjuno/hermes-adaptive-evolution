"""Portable R4 local boundary reproducer; Linux/root reviewed fixture only.

Requires --payload pointing to the cumulative implementation tree containing
forced_mediation.py and reviewed_canary.py. No real model, billing, or Hermes
configuration is touched.
"""
from __future__ import annotations
import argparse,json,os,shutil,socket,subprocess,sys,tempfile,threading,time,hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--payload',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
 if a.output.exists():raise ValueError('refuse existing output')
 payload=a.payload.resolve();sys.path.insert(0,str(payload))
 from adaptive_evolution_observer.campaign_budget import PLAN_SCHEMA
 from adaptive_evolution_observer.evidence_gate import digest
 from adaptive_evolution_observer.forced_mediation import SCHEMA,serve_worker,run_isolated_request
 from adaptive_evolution_observer.request_broker import CONFIG_SCHEMA,REQUEST_SCHEMA,initialize_broker,token_hash
 from adaptive_evolution_observer.reviewed_canary import PLAN_SCHEMA as CPLAN,approval_hash,execute,recover
 UID=GID=65534;TOK='d'*64;state={'gets':0,'posts':0}
 class H(BaseHTTPRequestHandler):
  def log_message(self,*x):pass
  def reply(self,o):
   raw=json.dumps(o).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_GET(self):state['gets']+=1;self.reply({'version':'reviewed'} if self.path=='/api/version' else {'models':[{'name':'reviewed','digest':'a'*64}]})
  def do_POST(self):self.rfile.read(int(self.headers.get('Content-Length','0')));state['posts']+=1;self.reply({'model':'reviewed','response':'{"value":1}','done':True,'done_reason':'stop','prompt_eval_count':10,'eval_count':5})
 srv=ThreadingHTTPServer(('127.0.0.1',0),H);srv.daemon_threads=True;th=threading.Thread(target=srv.serve_forever,daemon=True);th.start()
 with tempfile.TemporaryDirectory(dir=str(payload.parent)) as td:
  root=Path(td);root.chmod(0o755);auth=root/'authority';auth.mkdir(mode=0o700);ipc=root/'ipc';ipc.mkdir(mode=0o711)
  now=time.time_ns();p={'schema':'adaptive-evolution.local-text-pair-plan.v1','run_id':'r','endpoint':f'http://127.0.0.1:{srv.server_port}','provider_version':'reviewed','model':'reviewed','model_digest':'a'*64,'runtime_contract_hash':'b'*64,'max_calls':1,'max_total_tokens':100,'input_token_reserve':20,'output_token_limit':20,'socket_timeout_ms':1000,'run_deadline_ms':30000,'attempts_per_task':1,'policies':{'candidate':'c','baseline':'b'},'tasks':[{'task_id':'t','prompt':'x','expected':1}]}
  camp={'schema':PLAN_SCHEMA,'campaign_id':'c','max_calls':1,'max_total_tokens':100,'runs':[{'run_id':'r','plan_hash':digest(p),'max_calls':1,'max_total_tokens':100}]}
  bc={'schema':CONFIG_SCHEMA,'broker_id':'b','campaign':camp,'run_plans':[p],'not_before_ns':now-10**9,'expires_at_ns':now+20*10**9,'clients':[{'client_id':'w','credential_sha256':token_hash(TOK),'allowed_runs':['r']}]}
  mc={'schema':SCHEMA,'mediation_id':'m','broker_config':bc,'worker_uid':UID,'worker_gid':GID,'isolation_contract':{'network_namespace':'new_user_plus_net_namespace','separate_host_uid':True,'provider_route':'broker_only','socket_type':'filesystem_unix_stream'}}
  req={'schema':REQUEST_SCHEMA,'broker_hash':digest(bc),'client_id':'w','credential':TOK,'operation_id':'r:0:0:baseline'}
  db=auth/'db.sqlite3';initialize_broker(db,bc);os.chmod(db,0o600);sp=ipc/'b.sock';serv={}
  def broker():
   try:serv.update(serve_worker(mc,db,sp,authorized=True,max_connections=1,accept_timeout_s=5))
   except Exception as e:serv['error']=type(e).__name__+':'+str(e)
  bt=threading.Thread(target=broker,daemon=True);bt.start()
  for _ in range(200):
   if sp.exists():break
   time.sleep(.01)
  # Dangerous inheritable resources exist in parent; fixed launcher must close them.
  target=root/'operator.txt';target.write_text('SAFE');os.chmod(target,0o600);ffd=os.open(target,os.O_RDWR);os.set_inheritable(ffd,True)
  tcp=socket.socket();tcp.connect(('127.0.0.1',srv.server_port));os.set_inheritable(tcp.fileno(),True)
  isolated=run_isolated_request(mc,sp,req,authorized=True,timeout_s=4)
  os.close(ffd);tcp.close();bt.join(timeout=7)
  # Crash recovery of a local-state-only canary.
  cr=root/'canary';cr.mkdir(mode=0o700);(cr/'state.json').write_text('{"template":"solo"}\n');os.chmod(cr/'state.json',0o600)
  ct='e'*64;cp={'schema':CPLAN,'canary_id':'c','from_state':{'template':'solo'},'to_state':{'template':'one_leaf'},'effect_class':'local_state_only_no_external_effects','expires_at_ns':time.time_ns()+10**9,'approval_sha256':approval_hash(ct)}
  planfile=root/'cp.json';planfile.write_text(json.dumps(cp))
  code='import json,sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from adaptive_evolution_observer.reviewed_canary import execute;p=json.load(open(sys.argv[3]));execute(Path(sys.argv[2]),p,"e"*64,authorized=True,_fault="after_apply")'
  crash=subprocess.run([sys.executable,'-c',code,str(payload),str(cr),str(planfile)],capture_output=True,text=True,timeout=5)
  rec=recover(cr,cp);final=json.loads((cr/'state.json').read_text())
  result={'schema':'hermes.r4-portable-reproduction.v1','forced_mediation':{'reply':isolated['reply']['disposition'],'extra_fds':isolated['isolation']['initial_extra_fds'],'operator_file':target.read_text(),'provider_posts':state['posts']},'canary':{'crash_rc':crash.returncode,'recovery':rec,'state':final},'broker_service':serv,'real_model':False,'execution_authorized':False}
  result['passed']=isolated['reply']['disposition']=='ADMITTED' and isolated['isolation']['initial_extra_fds']==[] and target.read_text()=='SAFE' and state['posts']==1 and rec['phase']=='ROLLED_BACK' and final=={'template':'solo'}
 srv.shutdown();th.join(timeout=2);srv.server_close();result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 if not result['passed']:raise SystemExit(2)
if __name__=='__main__':main()
