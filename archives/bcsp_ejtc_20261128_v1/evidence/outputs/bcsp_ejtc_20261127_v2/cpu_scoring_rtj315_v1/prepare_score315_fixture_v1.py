"""Local asset binding and pending CPU fixture. No score computation."""
from pathlib import Path
import hashlib,json,sys
d=Path(__file__).resolve().parent;base=d.parent;project=base.parents[1]
h=lambda b:hashlib.sha256(b).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
native=base/'native_rtj315_preparation_v1';scope=json.loads((native/'EJTC_RTJ_D_native315_scope_v2.json').read_bytes())
rb=project/'outputs/bcsp_rbss_20261126_v2/foldd_native315_v1/RBSS_FoldD_native315_CPU_scoring_execution_request_v1.json';old=json.loads(rb.read_bytes())
indexrec=old['case_index'];idx=Path(indexrec['path']);assert rec(idx)==indexrec
index=json.loads(idx.read_bytes());assert [r['case_id'] for r in index['cases']]==scope['case_ids']
references=[]
for c,s in zip(index['cases'],scope['inputs']):
 assert c['normalization']==s['normalization'] and c['source_id']==s['source_id'] and c['point_file']['sha256']==s['input']['sha256']
 for k in ('reference','point_file'):
  p=Path(c[k]['path']);assert rec(p)==c[k];references.append(c[k])
backup=Path('E:/ResearchBackups/AdaPoinTr/BCSP_EJTC/2026-11-28_native_development_eval')
q=dict(schema='bcsp-ejtc-rtj-cpu-score-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,device='CPU',arms=['R','T','J'],seeds=scope['seeds'],
 counts=dict(model_rows=315,case_pairs=105,sources=21,comparisons=3,bootstrap_replicates=2000),
 bootstrap=dict(generator='PCG64',seed=2026112807,replicates=2000,source_count=21),case_ids=scope['case_ids'],source_ids=old['source_ids'],
 entry=rec(d/'ejtc_score315_v1.py'),interpreter=rec(Path(sys.executable)),numeric_versions=['1.26.4','1.13.1'],
 archive=rec(backup/'EJTC_RTJ_D_native315.tar.gz'),member_listing=rec(backup/'archive_members.json'),archive_checksum=rec(backup/'EJTC_RTJ_D_native315.tar.gz.sha256'),listing_checksum=rec(backup/'archive_members.json.sha256'),
 prediction_freeze=rec(native/'post_prediction_freeze_audit_v2/formal_post_prediction_freeze_audit_v2.json'),local_download_verification=rec(native/'local_download_verification_v2/local_download_verification_receipt_v2.json'),prediction_scope=rec(native/'EJTC_RTJ_D_native315_scope_v2.json'),prediction_request_sha256='4b9dc3dac44c4d547fb5c79826dc48346610a19ab828392c4fdbe1e98fcdec31',
 checkpoint_hashes={a:r['sha256'] for a,r in scope['checkpoints'].items()},case_index=indexrec,scorer=old['scorer'],metrics=old['metrics'],
 limits=dict(wall_seconds=3600,RSS_bytes=8589934592,output_bytes=2147483648),output=str(d/'cpu_scored_once_v1'),single_attempt=True,automatic_retry=False,formal_gate_executed_here=False,
 protocol=rec(project/'outputs/BCSP-EJTC_自由表面与共享切壁感知尾部覆盖监督_正式实验计划_2026-11-27_v2.md'),
 endpoint_policy=dict(original_frozen_score_prediction=True,world_mm=True,A1_area_weighted=True,A2_four_samples=True,far20='strict >20 mm',severe='dense E_P95_mm >20 OR dense J_Cover_at_2 ==0',alignment=False,point_filtering=False,gate_decision=False),
 supplementary_diagnostics=['dense J Cover@1','dense J Cover@3','dense J area (1,3] mm','dense J fraction (1,3] mm'],comparisons=['J_minus_R','J_minus_T','T_minus_R'])
for key in ('scorer','metrics'):assert rec(Path(q[key]['path']))==q[key]
write(d/'EJTC_CPU_scoring_request_fixture_v1.json',q)
write(d/'scoring_asset_preparation_receipt_v1.json',dict(status='LOCAL_SCORE_ASSET_BINDINGS_VERIFIED',case_index=rec(idx),reference_and_point_files_hashed=210,cases=105,sources=21,real_predictions_scored=0,server_operations=0,numeric_runtime='Existing adapointr CPU environment; no installs; exact runtime versions frozen in request',reference_bindings=references))
print(json.dumps(dict(status='LOCAL_SCORE_ASSET_BINDINGS_VERIFIED',hashed_files=210,real_scores=0)))
