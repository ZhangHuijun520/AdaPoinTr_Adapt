"""Targeted CPU contracts. Real archive validation, synthetic distance scoring only."""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,sys,tarfile,time
import numpy as np
d=Path(__file__).resolve().parent;out=d/'cpu_validation_v1';out.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('ejtc_score',d/'ejtc_score315_v1.py');q=json.loads((d/'EJTC_CPU_scoring_request_fixture_v1.json').read_bytes());raw=(d/'EJTC_CPU_scoring_request_fixture_v1.json').read_bytes();rid=h(raw)
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def put(p,v):p.write_text(json.dumps(v),encoding='utf-8');return rec(p)
checks=[]
def check(name,fn):
 try:detail=fn();checks.append(dict(check=name,status='PASS',detail=detail))
 except BaseException as e:
  checks.append(dict(check=name,status='FAIL',error=repr(e)));put(out/'failed_checks.json',checks);raise
 print('PASS '+name,flush=True)
def reject(fn):
 try:fn()
 except (ValueError,KeyError,FileExistsError):return True
 raise AssertionError('Invalid fixture accepted')
auth=dict(schema='bcsp-development-authorization-v1',request_sha256=rid,explicit_user_authorization=True,user_authorization_text='Artificial CPU fixture only '+rid)
check('S01_exact_authorize',lambda:w.authorize(q,rid,auth))
def changed(key,val):
 x=copy.deepcopy(q);x[key]=val;return reject(lambda:w.authorize(x,rid,auth))
check('S02_extra_row_budget_rejected',lambda:changed('counts',dict(q['counts'],model_rows=316)))
check('S03_wrong_arm_order_rejected',lambda:changed('arms',['R','J','T']))
check('S04_wrong_bootstrap_seed_rejected',lambda:changed('bootstrap',dict(q['bootstrap'],seed=2026112707)))
check('S05_missing_exact_authorization_rejected',lambda:reject(lambda:w.authorize(q,rid,dict(auth,user_authorization_text='missing'))))
arc=w.archive_members(q);index=json.loads(w.exact(q['case_index']));scope=json.loads(w.exact(q['prediction_scope']));manifest=[json.loads(r) for r in arc['manifest.jsonl'].splitlines()]
check('S06_real_archive_320_frozen_members',lambda:len(arc))
check('S07_real_105_cases_315_identity_pairing',lambda:len(w.index_cases(q,scope,index,manifest)[1]))
def corrupt_manifest(key,value):
 x=copy.deepcopy(manifest);x[105][key]=value;return reject(lambda:w.index_cases(q,scope,index,x))
check('S08_wrong_checkpoint_rejected',lambda:corrupt_manifest('checkpoint_sha256','0'*64))
check('S09_coordinate_drift_rejected',lambda:corrupt_manifest('normalization',dict(center=[0,0,0],scale=1)))
check('S10_duplicate_or_wrong_case_rejected',lambda:corrupt_manifest('case_id',manifest[0]['case_id']+'wrong'))
def all_payloads():
 for r in manifest:w.verify_payload(arc[r['member']])
 return dict(decoded=315,real_distance_scores=0)
check('S11_all315_real_payload_shapes_and_indices',all_payloads)
actual=w.verify_payload(arc[manifest[0]['member']])
def bad_payload(key,value):
 v={k:a.copy() for k,a in actual.items()};v[key]=value;b=io.BytesIO();np.savez_compressed(b,**v);return reject(lambda:w.verify_payload(b.getvalue()))
check('S12_NaN_rejected',lambda:bad_payload('prediction',np.full((8192,3),np.nan,np.float32)))
check('S13_parent_index_drift_rejected',lambda:bad_payload('parent_index',np.zeros(8192,np.int64)))
check('S14_coarse_S_delta_drift_rejected',lambda:bad_payload('coarse',actual['coarse']+1))
core=w.module(q['scorer']);metric=w.module(q['metrics'])
ref=dict(a_centers=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],np.float64),a_weights=np.array([1,2,3,4],np.float64),a_is_j=np.array([False,False,True,True]),a_axes=np.array([0,0,1,2]),affine=np.eye(3),origin=np.zeros(3))
gt=np.tile(ref['a_centers'].astype(np.float32),(2048,1));coarse=np.tile(ref['a_centers'].astype(np.float32),(64,1));prediction=np.repeat(coarse,32,axis=0)
art=dict(coarse=coarse,prediction=prediction,S=coarse.copy(),delta=np.zeros_like(coarse),parent_index=np.repeat(np.arange(256,dtype=np.int64),32),token_index=np.arange(256,dtype=np.int64))
norm=dict(center=[0,0,0],scale=1);a2,_,_=metric.a2_reference(ref)
base=core.score_prediction(metric,art,ref,a2,gt,norm)
observed=w.score_one(core,metric,art,ref,a2,gt,norm)
def metric_equivalence():
 x=copy.deepcopy(observed);x.pop('diagnostics');assert x==base
 assert base['dense']['CD_L1_mm']==0 and base['dense']['E_Cover_at_2']==base['dense']['J_Cover_at_2']==1 and base['severe_geometry'] is False
 return 'Frozen core result unchanged; only preregistered diagnostic fields appended'
check('S15_frozen_core_exact_synthetic_equivalence',metric_equivalence)
def band_boundary():
 r=dict(a_is_j=np.ones(4,bool),a_weights=np.array([1,2,3,4],np.float64));v=w.diagnostic(metric,r,np.array([1.,2.,3.,3.00001]))
 assert v['J_Cover_at_1']==.1 and v['J_Cover_at_3']==.6 and v['J_area_1_to_3_mm2']==5 and v['J_fraction_1_to_3']==.5
 return 'Strict (1,3] band and inclusive cover thresholds, area weighted'
check('S16_preregistered_J_diagnostic_boundaries',band_boundary)
def bootstrap_contract():
 a=w.bootstrap();b=np.random.Generator(np.random.PCG64(2026112807)).integers(0,21,size=(2000,21),dtype=np.int64)
 assert a.shape==(2000,21) and a.dtype==np.int64 and np.array_equal(a,b)
 return h(a.tobytes())
check('S17_shared_bootstrap_seed_and_indices',bootstrap_contract)
synthetic=[]
for arm,delta in [('R',0),('T',1),('J',2)]:
 for r in index['cases']:
  v=copy.deepcopy(base);v['dense']['CD_L1_mm']+=delta;v['dense']['J_Cover_at_2']-=delta*.01
  synthetic.append(dict(arm=arm,case_id=r['case_id'],source_id=r['source_id'],**v))
def compare_signs():
 for a,b in [('J','R'),('J','T'),('T','R')]:
  result=w.comparison(core,synthetic,q['source_ids'],w.bootstrap(),a,b)
  assert len(result['pairs'])==105 and result['summary']['arm_aliases']=={'A':a,'B':b}
  want={('J','R'):2,('J','T'):1,('T','R'):1}[a,b]
  assert result['summary']['metrics']['dense']['CD_L1_mm']['delta_A_minus_B']==want
  assert abs(result['summary']['metrics']['dense']['J_Cover_at_2']['delta_A_minus_B']+want)<1e-12
 return 'Three left-minus-right signs and coverage pp units verified'
check('S18_three_pair_aliases_signs_and_units',compare_signs)
def resource_rejection():
 from types import SimpleNamespace
 proc=SimpleNamespace(memory_info=lambda:SimpleNamespace(rss=999))
 reject(lambda:w.resource_check(time.monotonic(),dict(wall_seconds=1,RSS_bytes=1,output_bytes=100),proc,out))
 proc=SimpleNamespace(memory_info=lambda:SimpleNamespace(rss=0))
 reject(lambda:w.resource_check(time.monotonic()-2,dict(wall_seconds=1,RSS_bytes=1,output_bytes=100),proc,out))
 return True
check('S19_RSS_and_wall_fail_closed',resource_rejection)
# Actual full score loop uses artificial references/payloads and a distance-call sentinel.
buf=io.BytesIO();np.savez_compressed(buf,**art);art_raw=buf.getvalue()
pr=out/'synthetic_points.npz';np.savez_compressed(pr,implant=gt)
rf=out/'synthetic_reference.npz';np.savez_compressed(rf,**ref)
fake_scope=copy.deepcopy(scope);fake_index=copy.deepcopy(index);fake_manifest=copy.deepcopy(manifest)
for c,s in zip(fake_index['cases'],fake_scope['inputs']):
 c.update(normalization=norm,point_file=rec(pr),reference=rec(rf),target_array_sha256=h(gt.tobytes()))
 s.update(normalization=norm);s['input']['sha256']=h(pr.read_bytes())
for r in fake_manifest:
 r.update(normalization=norm,input_sha256=h(pr.read_bytes()),bytes=len(art_raw),sha256=h(art_raw))
fq=copy.deepcopy(q);fq['prediction_scope']=put(out/'synthetic_scope.json',fake_scope);fq['case_index']=put(out/'synthetic_index.json',fake_index);fq['_request_sha256']='SYNTHETIC_CPU_TEST'
fake_arc={r['member']:art_raw for r in fake_manifest}
fake_arc.update({n:arc[n] for n in ('started.json','attempts.jsonl','inference_complete.json','resources.jsonl')});fake_arc['manifest.jsonl']=b'\n'.join(json.dumps(r).encode() for r in fake_manifest)
calls=[]
def full_loop():
 target=out/'synthetic_full_loop';target.mkdir();old=(w.archive_members,w.score_one)
 def sentinel(*args):calls.append(1);return copy.deepcopy(observed)
 try:w.archive_members=lambda q:dict(fake_arc);w.score_one=sentinel;w.score(fq,target)
 finally:w.archive_members,w.score_one=old
 rows=[json.loads(x) for x in (target/'model_scores.jsonl').read_bytes().splitlines()]
 assert len(rows)==len(calls)==315 and {r['arm'] for r in rows}=={'R','T','J'}
 assert set(json.loads((target/'paired_summary.json').read_bytes()))=={'J_minus_R','J_minus_T','T_minus_R'}
 assert np.array_equal(np.load(target/'source_bootstrap_indices.npy'),w.bootstrap())
 assert len(list(target.iterdir()))==5 and not (target/'failure.json').exists()
 return dict(artificial_score_sentinel_calls=315,real_prediction_scores=0)
check('S20_actual315_score_loop_and_three_summaries',full_loop)
def actual_main():
 x=copy.deepcopy(q);x['output']=str(out/'actual_main_fixture');raw=json.dumps(x).encode();sha=h(raw)
 qr=out/'main_request.json';qr.write_bytes(raw);ar=out/'main_authorization.json';ar.write_text(json.dumps(dict(auth,request_sha256=sha,user_authorization_text='CPU fixture only '+sha)),encoding='utf-8')
 argv=['fixture','--request',str(qr),'--request-sha256',sha,'--authorization',str(ar),'--authorization-sha256',h(ar.read_bytes())];old=(sys.argv,w.score);call=[]
 try:sys.argv=argv;w.score=lambda x,p:call.append((x,p));w.main()
 finally:sys.argv,w.score=old
 assert len(call)==1 and call[0][0]['_request_sha256']==sha
 return 'Actual main authorization/entry/interpreter/fresh-output path; no real score'
check('S21_actual_main_startup_path',actual_main)
def failure_path():
 x=copy.deepcopy(q);x['output']=str(out/'actual_main_failure_fixture');raw=json.dumps(x).encode();sha=h(raw);qr=out/'failure_request.json';qr.write_bytes(raw);ar=out/'failure_auth.json';ar.write_text(json.dumps(dict(auth,request_sha256=sha,user_authorization_text=sha)),encoding='utf-8')
 old=(sys.argv,w.score)
 def fail(*a):raise ValueError('ARTIFICIAL_SCORE_FAILURE')
 try:
  sys.argv=['fixture','--request',str(qr),'--request-sha256',sha,'--authorization',str(ar),'--authorization-sha256',h(ar.read_bytes())];w.score=fail
  assert reject(w.main)
 finally:sys.argv,w.score=old
 assert json.loads((Path(x['output'])/'failure.json').read_bytes())['status']=='FAILED_STOP_NO_RETRY'
 return True
check('S22_actual_failure_evidence_no_retry',failure_path)
receipt=dict(status='EJTC_SCORE315_TARGETED_CPU_VALIDATION_PASS',passed=len(checks),checks=checks,entry=rec(d/'ejtc_score315_v1.py'),test=rec(Path(__file__)),real_archive_payloads_validated=315,real_prediction_distance_scores=0,synthetic_full_loop_calls=315,torch_imported='torch' in sys.modules,server_operations=0,
 limitations=['Actual geometry equivalence checked on synthetic reference only; no real-case distance scores computed','Full 315-row loop uses artificial reference files and explicit score sentinel','CPU contracts do not establish scientific improvement'])
assert receipt['torch_imported'] is False
put(out/'CPU_validation_receipt_v1.json',receipt)
print(json.dumps(dict(status=receipt['status'],passed=len(checks),real_prediction_scores=0)))
