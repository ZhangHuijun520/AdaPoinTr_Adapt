"""Summarize existing observation only; no server calls or result scoring."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;A=N/'authorized_execution_v1'
report_path=A/'completion_observation_v1/report.json'
r=json.loads(report_path.read_bytes());c=r['inference_complete'];done=r['completion']
assert r['exit_code']=='0' and not r['session_alive'] and r['prediction_records']==420 and r['failure'] is None
assert c['forwards']==420 and len(c['models'])==4 and all(x['forwards']==105 and x['state_before']==x['state_after'] for x in c['models'])
assert all(c[k]==0 for k in ['training_updates','BNCal','loss','backward'])
result=dict(status='420_PREDICTIONS_COMPLETED_OBSERVED_PENDING_FORMAL_FREEZE_AUDIT',
 outer_execution_request_sha256='85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea',
 inner_entry_request_sha256=c['request_sha256'],evidence=dict(path=str(report_path),bytes=report_path.stat().st_size,sha256=hashlib.sha256(report_path.read_bytes()).hexdigest()),
 exit_code=0,total_forwards=420,models=c['models'],archive_receipt={k:v for k,v in done['archive'].items() if k!='members'},
 training_updates=0,BNCal=0,loss=0,backward=0,retries=0,formal_freeze_audit_performed=False,
 archive_hash_independently_recomputed_by_observer=False,downloaded_to_Windows=False,local_scoring_performed=False,
 next_stage='Separate formal read-only post-prediction freeze audit;verified manual download;fixed local CPU scoring under its bound execution scope')
with (A/'execution_completion_observed_v1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k not in ['models','evidence']}))
