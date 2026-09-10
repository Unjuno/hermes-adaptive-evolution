"""Reviewed loopback API-scope control. No model/billing or OS sandbox claim.
Requires --payload from the cumulative conversation package.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys,tempfile,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--payload',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.exists():raise ValueError('refuse existing output')
    payload=args.payload.resolve();sys.path.insert(0,str(payload))
    from adaptive_evolution_observer.request_broker import (RequestBroker,initialize_broker,
        CONFIG_SCHEMA,REQUEST_SCHEMA,token_hash)
    from adaptive_evolution_observer.campaign_budget import PLAN_SCHEMA
    from adaptive_evolution_observer.evidence_gate import digest
    from adaptive_evolution_observer.shadow_io import ShadowContractError
    state={'posts':0,'gets':0}
    class H(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def reply(self,body):
            raw=json.dumps(body).encode();self.send_response(200)
            self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            state['gets']+=1
            self.reply({'version':'reviewed'} if self.path=='/api/version' else
                       {'models':[{'name':'reviewed','digest':'a'*64}]})
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']));state['posts']+=1
            self.reply({'model':'reviewed','response':'{"value":1}','done':True,'done_reason':'stop',
                        'prompt_eval_count':10,'eval_count':5})
    srv=ThreadingHTTPServer(('127.0.0.1',0),H);srv.daemon_threads=True
    thread=threading.Thread(target=srv.serve_forever,kwargs={'poll_interval':.01});thread.start()
    try:
        a=json.loads((payload/'examples/campaign_run_a.json').read_text())
        a.update(run_id='a',endpoint=f'http://127.0.0.1:{srv.server_port}',provider_version='reviewed',
            model='reviewed',model_digest='a'*64,max_calls=4,max_total_tokens=600,
            run_deadline_ms=60000,tasks=[{'task_id':'t0','prompt':'extract 1','expected':1}],attempts_per_task=1)
        b=copy.deepcopy(a);b['run_id']='b'
        campaign={'schema':PLAN_SCHEMA,'campaign_id':'one','max_calls':2,'max_total_tokens':600,
            'runs':[{'run_id':p['run_id'],'plan_hash':digest(p),'max_calls':p['max_calls'],
                     'max_total_tokens':p['max_total_tokens']} for p in (a,b)]}
        # Fixed TEST credentials, not deployment keys.
        tokens={'alice':'1'*64,'bob':'2'*64};start=time.time_ns()-10**8
        cfg={'schema':CONFIG_SCHEMA,'broker_id':'one','campaign':campaign,'run_plans':[a,b],
            'not_before_ns':start,'expires_at_ns':start+60*10**9,
            'clients':[{'client_id':c,'credential_sha256':token_hash(tokens[c]),'allowed_runs':[r]}
                       for c,r in [('alice','a'),('bob','b')]]}
        def request(client='alice',op='a:0:0:baseline',**extra):
            return dict(schema=REQUEST_SCHEMA,broker_hash=digest(cfg),client_id=client,
                        credential=tokens[client],operation_id=op,**extra)
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'authority.db';initialize_broker(db,cfg)
            with RequestBroker(db,cfg) as broker:
                denied=0
                for bad in (request(db='replacement.db'),request(actual_tokens=0),
                            request(payload={'prompt':'changed'}),request(op='b:0:0:baseline')):
                    try:broker.execute(bad)
                    except ShadowContractError:denied+=1
                before=dict(state)
                first=broker.execute(request())
                second=broker.execute(request(op='a:0:0:candidate'))
                capped=broker.execute(request('bob','b:0:0:baseline'))
                replay=broker.execute(request())
        assert denied==4 and before=={'posts':0,'gets':0}
        assert first['disposition']==second['disposition']=='ADMITTED'
        assert capped['disposition']=='BLOCKED_CAMPAIGN_BUDGET' and state['posts']==2
        assert replay['disposition']=='REPLAY_NO_SEND' and replay['receipt_hash']==first['receipt_hash']
        result={'schema':'hermes.broker-scope-reproduction.v1','denied':denied,'wire_before_valid':before,
            'posts':state['posts'],'capped':capped['disposition'],'replay':replay['disposition'],
            'scope':'actual reviewed HTTP; direct broker API, not UDS client separation',
            'real_model':False,'execution_authorized':False,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'implementation_sha256':hashlib.sha256((payload/'adaptive_evolution_observer/request_broker.py').read_bytes()).hexdigest()}
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    finally:srv.shutdown();thread.join(timeout=2);srv.server_close()

if __name__=='__main__':main()
