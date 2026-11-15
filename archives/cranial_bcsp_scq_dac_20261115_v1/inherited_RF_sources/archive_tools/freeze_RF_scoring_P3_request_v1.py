"""Freeze local CPU scoring P3/request only; never invokes real score execution."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_score_impl_20261115_v1';PRE=R/'outputs/scq_rf_score_prep_20261115_v1';F=R/'outputs/scq_rf_pred_freeze_20261115_v2'
OLD=R/'outputs/scq_score_impl_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
entry=S/'bcsp_scq_rf_three_arm_score_v1.py';test=S/'test_RF_three_arm_score_cpu_v1.py';cpu=S/'CPU_contract_v1/result_v1.json';result=read(cpu)
assert result['status']=='RF_THREE_ARM_SCORING_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==48 and result['real_score_rows']==0 and not (cpu.parent/'failure_v1.json').exists()
assert result['synthetic_actual_metric_rows']==10 and result['synthetic_orchestrated_rows']==1050
for r in result['source_bindings']:exact(r)
static=read(S/'static_review_v1.json');assert static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
for r in static['files']:assert sha(S/r['name'])==r['sha256']
oldq=read(OLD/'local_scoring_execution_request_v1.json');exact(oldq['environment']['python']);exact(oldq['implementation']['metrics'])
assert result['python']==oldq['environment']['python_version'] and result['packages']==oldq['environment']['packages']
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
a,b=nodes(OLD/'bcsp_scq_BS_two_arm_score_v1.py'),nodes(entry)
changed=[n for n in b if a[n]!=b[n]];assert set(changed)=={'authorize','validate_index','validate_archive','load_prediction_arrays','run_scoring','main'}
keep=[n for n in b if n not in changed];assert all(a[n]==b[n] for n in keep)
index=read(PRE/'RF_three_arm_score_case_index_candidate_v1.json');scope=read(PRE/'RF_three_arm_unified_CPU_scoring_scope_v1.json');v=read(PRE/'local_archive_verification_v1.json')
assert v['status']=='LOCAL_SCQ_RF_FOUR_FILES_ALL636_MEMBERS_VERIFIED'
for r in v['files']:exact(r)
assert index['counts']==scope['counts']==dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210)
protocol=copy.deepcopy(scope);protocol.update(status='FROZEN_PENDING_SEPARATE_SCORING_EXECUTION_AUTHORIZATION',schema='bcsp-scq-rf-local-scoring-protocol-v1')
emit(S/'frozen_scoring_protocol_v1.json',protocol)
baseline=oldq['frozen_baseline_scores'];basefile=exact(baseline)
controls=[r for r in map(json.loads,basefile.read_text(encoding='utf-8').splitlines()) if r['arm'] in ['Nop_D','GT_8192']]
assert len(controls)==len({(r['fold'],r['arm'],r['case_id']) for r in controls})==420
assert {(r['fold'],r['arm'],r['case_id']) for r in controls}=={(c['fold'],arm,c['case_id']) for c in index['cases'] for arm in ['Nop_D','GT_8192']}
checks=dict(three_fixed_comparisons_and_D_device_qualification_preserved=True,verified_archive_footprint_bound=True,final_source_CPU_static_bound=True,full_authorize_counts_pair_negative_cases=True,actual210_case630_prediction_metadata=True,one_RF_archive_exact636_members=True,strict_nine_keys_and_RF_stage_equations=True,native_construction_state_RNG_provenance_guard=True,all_metric_risk_source_pair_functions_AST_unchanged=True,synthetic1050_case210_source_orchestration=True,shared420_controls_once_and_exact_frozen_values=True,control_drift_stops_no_false_completion=True,first_error_no_next_case=True,undefined_pairs_and_all_severe_cases_retained=True,CPU_environment_metric_hash_exact=True,downloaded_archive_hashes_verified=True,no_real_scoring_or_GPU=True)
p3=dict(status='LOCAL_SCQ_RF_SCORING_P3_PASS',date='2026-11-15',scorer=rec(entry),test=rec(test),CPU_result=rec(cpu),CPU_tests=48,static_review=rec(S/'static_review_v1.json'),parent=rec(OLD/'bcsp_scq_BS_two_arm_score_v1.py'),metric=oldq['implementation']['metrics'],unchanged_AST_functions=keep,changed_functions=changed,checks=checks,real_score_rows=0,synthetic_actual_metric_rows=10,synthetic_orchestrated_rows=1050,server_operations=0,GPU_calls=0,limitations=result['limitations']+['Source-equal descriptive C/D single-seed comparisons only; no bootstrap/pvalue/formal gate.','GT and real predictions not decoded during implementation; no SCQ efficacy claim.'])
emit(S/'implementation_P3_v1.json',p3)
q=copy.deepcopy(oldq);q.update(schema='bcsp-scq-rf-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-15',purpose='Frozen Native SCQ-RF S-ref/Static/Requery C/D CPU scores; no new inference',implementation=dict(scorer=rec(entry),metrics=oldq['implementation']['metrics']),output=str((S/'unified_scores_v1').resolve()),counts=index['counts'],score_case_index=rec(PRE/'RF_three_arm_score_case_index_candidate_v1.json'),P3=rec(S/'implementation_P3_v1.json'),frozen_baseline_scores=baseline)
pi=F/'downloads/installed/RF_sixmodel_input_index_v2.json';pp=F/'downloads/installed/RF_sixmodel_native_scope_v1.json'
q['prediction_index']=rec(pi)
q['archive_inputs']={'SCQ_RF':dict(archive=v['files'][0],sidecars=v['files'][1:],prediction_index=rec(pi),prediction_protocol=rec(pp),prediction_request_sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')}
q['evidence']=dict(formal_RF_prediction_audit=rec(F/'post_prediction_freeze_audit_result_v1.json'),local_archive_verified=rec(PRE/'local_archive_verification_v1.json'),preparation_receipt=rec(PRE/'preparation_validation_receipt_v1.json'),compatibility_review=rec(PRE/'scorer_compatibility_review_v1.json'),CPU_contracts=rec(cpu),P3=rec(S/'implementation_P3_v1.json'),frozen_scoring_protocol=rec(S/'frozen_scoring_protocol_v1.json'),frozen_shared_control_rows=baseline)
q['comparison_qualification']=scope['comparison_qualification']
q['scientific_contract']=dict(arms=['S-ref','RF-Static','RF-Requery'],controls=['Nop_D','GT_8192'],pairs=[['RF-Static','RF-Requery'],['S-ref','RF-Static'],['S-ref','RF-Requery']],delta='candidate minus baseline; negative error and positive coverage indicate improvement',primary='A1 area-weighted E_P95; five defects/source then21 sources equally/fold',geometry=oldq['scientific_contract']['geometry'],risk=oldq['scientific_contract']['risk'],alignment='Native world mm; no GT registration/ICP/postfilter',coarse='Actual Qused256 and P8192 in all630 Native predictions; validate nine saved keys and stage equations without replacing Native output',baseline_archive_handling='One frozen RF archive;630 model rows plus420 shared controls once/case; recomputed controls must exactly equal previously frozen values',diagnostic_cache='No context/full decoder trace; exact empty cache log only',archive_member_byte_limit=scope['archive_binding']['uncompressed_member_bytes'],comparison_qualification=scope['comparison_qualification'])
q['future_authorization']=dict(path=str((S/'authorized_execution_v1/score_authorization_v1.json').resolve()),schema='bcsp-scq-rf-score-authorization-v1')
q['invocation_contract']['readiness']='Rehash scorer/metric/evidence/RFarchive/3sidecars/frozen control scores/CPU Python/210references/210points; exact output/control paths absent'
q['invocation_contract']['startup_mode']='Foreground managed execution retaining tool process session; no detached subprocess startup'
q['completion_boundary']='Separate formal read-only post-score freeze audit before RF three-arm effect interpretation'
q['limits']=protocol['limits'];q['forbidden']=protocol['prohibited']
assert not Path(q['output']).exists() and not Path(q['future_authorization']['path']).parent.exists()
for r in q['evidence'].values():exact(r)
spec=importlib.util.spec_from_file_location('SCQ_final_authorize_AST',entry)
# Final authorization contract runs in memory from the actual source function;
# avoid importing numpy/metric or running any scientific function in this freezer.
tree=ast.parse(entry.read_text(encoding='utf-8'));fn=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['require','authorize']]
env=dict(json=json,ARMS=['S-ref','RF-Static','RF-Requery'],PAIRS=[('RF-Static','RF-Requery'),('S-ref','RF-Static'),('S-ref','RF-Requery')],CONTROLS=['Nop_D','GT_8192'],QUALIFICATION=scope['comparison_qualification'])
exec(compile(ast.Module(fn,[]),'actual_scq_authorize_only','exec'),env)
req=S/'local_scoring_execution_request_v1.json';emit(req,q);rh=sha(req)
class Mem:
 def __init__(self,v):self.v=v
 def read_bytes(self):return json.dumps(self.v).encode()
memory={'Q':Mem(q),'A':Mem(dict(schema='bcsp-scq-rf-score-authorization-v1',request_sha256=rh,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_MEMORY_ONLY'))}
env['check']=lambda r:memory[r['path']]
assert env['authorize'](dict(path='Q',sha256=rh),dict(path='A'))==q
emit(S/'request_preparation_receipt_v1.json',dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rec(req),P3=rec(S/'implementation_P3_v1.json'),counts=q['counts'],CPU_tests=48,requires_upload=False,execution_materialized=False,real_scoring_executed=False))
print(json.dumps(dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rec(req),CPU_tests=48,counts=q['counts'],requires_upload=False),ensure_ascii=False))
