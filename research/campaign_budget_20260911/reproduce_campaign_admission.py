"""Use the delivered payload to reproduce local admission; no network or model calls."""
from __future__ import annotations
import argparse,copy,hashlib,json,sys,tempfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--payload',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.exists():raise ValueError('refuse existing output')
    payload=args.payload.resolve()
    if not (payload/'adaptive_evolution_observer/campaign_budget.py').is_file():
        raise ValueError('requires the cumulative campaign implementation payload')
    sys.path.insert(0,str(payload))
    from adaptive_evolution_observer.campaign_budget import CampaignBudget,PLAN_SCHEMA
    from adaptive_evolution_observer.provider_budget import ProviderBudget
    from adaptive_evolution_observer.evidence_gate import digest
    from adaptive_evolution_observer.shadow_io import ShadowContractError
    plans=[]
    for name in ['a','b']:
        plans.append({'schema':'adaptive-evolution.local-text-pair-plan.v1','run_id':name,
            'endpoint':'http://127.0.0.1:11434','provider_version':'reviewed','model':'reviewed',
            'model_digest':'a'*64,'runtime_contract_hash':'b'*64,'max_calls':2,
            'max_total_tokens':100,'input_token_reserve':10,'output_token_limit':10,
            'socket_timeout_ms':1000,'run_deadline_ms':1000,'attempts_per_task':1,
            'policies':{'candidate':'Return JSON','baseline':'Return value'},
            'tasks':[{'task_id':'one','prompt':'extract 1','expected':1}]})
    campaign={'schema':PLAN_SCHEMA,'campaign_id':'frozen','max_calls':2,'max_total_tokens':200,
        'runs':[{'run_id':p['run_id'],'plan_hash':digest(p),'max_calls':2,'max_total_tokens':100} for p in plans]}
    h=digest({'reviewed_input':1});out={}
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        for unknown in [False,True]:
            cell={}
            for shared in [False,True]:
                key=f'{unknown}-{shared}';admitted=[];decisions=[]
                if shared:CampaignBudget.initialize(root/f'{key}.db',campaign)
                for p in plans:
                    owner=CampaignBudget(root/f'{key}.db',campaign) if shared else None
                    b=owner.bind(p) if owner else ProviderBudget(root/f'{key}-{p["run_id"]}.db',plan_hash=digest(p),max_calls=2,max_tokens=100)
                    try:
                        for i in range(1 if unknown else 2):
                            rid=f'{p["run_id"]}:{i}';r=b.reserve(rid,h,20);decisions.append(r)
                            if r=='ADMITTED':
                                admitted.append(rid)
                                b.settle(rid,h,None if unknown else 10,{'request_id':rid,'payload_hash':h})
                    finally:
                        if owner:owner.close()
                        else:b.close()
                cell['shared' if shared else 'per_run']={'admissions':len(admitted),'decisions':decisions}
            out['unknown' if unknown else 'completed']=cell
        path=root/'projection-study.db';CampaignBudget.initialize(path,campaign)
        with CampaignBudget(path,campaign) as db:
            view=db.bind(plans[0]);view.reserve('a:0',h,20)
            view.settle('a:0',h,10,{'request_id':'a:0','payload_hash':h})
            report=view.report();target=root/'projection';target.mkdir()
            view.export_audit_projection(target,report)
        refused=False
        try:
            with ProviderBudget(target/'budget.sqlite3',plan_hash=digest(plans[0]),max_calls=2,max_tokens=100):pass
        except ShadowContractError:refused=True
        out['audit_projection_refused_as_admission']=refused
    assert out['completed']['per_run']['admissions']==4
    assert out['completed']['shared']['admissions']==2
    assert out['unknown']['per_run']['admissions']==2
    assert out['unknown']['shared']['admissions']==1
    assert out['audit_projection_refused_as_admission']
    out.update(schema='hermes.campaign-budget-reproducer.v1',network_used=False,real_model=False,
        execution_authorized=False,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        implementation_sha256=hashlib.sha256((payload/'adaptive_evolution_observer/campaign_budget.py').read_bytes()).hexdigest())
    args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
