"""Freeze local two-arm scorer P3 and pending request; no real scoring."""
import ast,copy,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent;PRE=B/'lqi_F0_scoring_preparation_v1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def read(p):return json.loads(p.read_bytes())
def exact(r):
 p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def emit(n,v):
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
entry=S/'bcsp_lqi_F0_two_arm_score_v1.py';test=S/'test_lqi_F0_score_cpu_v2.py';cpu=S/'artificial_cpu_batch_v2/result_v1.json';result=read(cpu)
assert result['status']=='LQI_F0_SCORING_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==50 and result['real_score_rows']==0
assert result['synthetic_actual_metric_rows']==12 and result['synthetic_orchestrated_rows']==840 and not (cpu.parent/'failure_v1.json').exists()
for r in result['source_bindings']:exact(r)
static=read(S/'static_review_v2.json');assert static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
for r in static['files']:assert sha(S/r['name'])==r['sha256']
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
parent=B/'Native_scoring_implementation_v1/bcsp_f0_T0_M0_three_arm_score_v1.py';a,b=funcs(parent),funcs(entry)
keep=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','score_case','aggregate_source','describe_pairs','paired_summary','case_differences','defect_summary','csv_rows','risk_transitions']
assert all(a[n]==b[n] for n in keep)
changed=[n for n in b if n not in a or a[n]!=b[n]];assert set(changed)=={'authorize','validate_index','validate_archive','run_scoring','main'}
old=read(B/'Native_scoring_implementation_v1/local_scoring_execution_request_v1.json');exact(old['implementation']['metrics']);exact(old['environment']['python'])
assert result['python']==old['environment']['python_version'] and result['packages']==old['environment']['packages']
index=read(PRE/'LQI_F0_score_case_index_candidate_v1.json');scope=read(PRE/'LQI_F0_unified_scoring_scope_v1.json')
verification=read(PRE/'local_LQI_and_F0_archive_verification_v1.json');assert verification['status']=='LOCAL_LQI_AND_F0_BACKUPS_VERIFIED'
for archive in verification['archives']:
 for r in archive['files']:exact(r)
assert index['counts']==scope['counts']==dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168)
protocol=copy.deepcopy(scope);protocol.update(status='FROZEN_PENDING_SEPARATE_SCORING_EXECUTION_AUTHORIZATION',schema='bcsp-lqi-F0-two-arm-local-scoring-protocol-v1')
emit('frozen_scoring_protocol_v1.json',protocol)
gaps=read(PRE/'entry_compatibility_and_baseline_bindings_v1.json')
baseline=next(r for r in gaps['frozen_F0_and_shared_control_rows'] if Path(r['path']).name=='case_metrics.jsonl');exact(baseline)
checks=dict(final_scorer_and_test_match_CPU_static=True,actual210_case_metadata420_prediction_bindings=True,full_authorize_and_wrong_pair_counts_denied=True,both246_F0_and216_LQI_archive_readers=True,zero_byte_exception_only_exact_LQI_cache_manifest=True,wrong_model_hash_checkpoint_and_RNG_denied=True,all420_dense_and_coarse_tensors_available=True,all_metric_risk_position_source_pair_functions_AST_unchanged=True,source_equal_840_case168_source_orchestration=True,LQI_minus_F0_direction_and_new_rescued_cases=True,undefined_pairs_kept_no_case_drop=True,strict_frozen630_F0_and_control_value_match_before_completion=True,baseline_drift_stops_without_false_completion=True,first_case_failure_stops_no_retry=True,backup_not_extracted_or_modified=True,no_Torch_GPU_network_model_training_imports=True,CPU_environment_and_metric_exact=True,failed_v1_fixture_retained_production_unchanged=True)
p3=dict(status='LOCAL_LQI_F0_SCORING_P3_PASS',date='2026-11-11',scorer=rec(entry),test=rec(test),CPU_result=rec(cpu),CPU_tests=50,static_review=rec(S/'static_review_v2.json'),parent=rec(parent),metric=old['implementation']['metrics'],unchanged_AST_functions=keep,changed_functions=changed,checks=checks,real_score_rows=0,synthetic_actual_metric_rows=12,synthetic_orchestrated_rows=840,server_operations=0,GPU_calls=0,limitations=result['limitations']+['First CPU batch stopped on obsolete fixture dictionary lookup; only test parameter corrected in v2; production scorer unchanged','Artificial full-row orchestration is not840 real metric computations; actual metric used only12 artificial rows','Native scientific accuracy awaits separately authorized real CPU scoring and post-scoring freeze audit','Only two folds and one seed; source equal descriptive analysis, no bootstrap/pvalue/formal gate'])
emit('implementation_P3_v1.json',p3)
q=copy.deepcopy(old)
q.update(schema='bcsp-lqi-F0-two-arm-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,purpose='Frozen Native LQI/F0 twofold paired CPU scores; no new inference',implementation=dict(scorer=rec(entry),metrics=old['implementation']['metrics']),output=str((S/'unified_scores_v1').resolve()),counts=index['counts'],score_case_index=rec(PRE/'LQI_F0_score_case_index_candidate_v1.json'),P3=rec(S/'implementation_P3_v1.json'),frozen_baseline_scores=baseline)
q['archive_inputs']={'F0':copy.deepcopy(old['archive_inputs']['F0'])}
records=index['archive_inputs']['LQI'];lqi_index=B/'lqi_native_prediction_implementation_v1/pending_request_final_v1/transport_payload/LQI_CD_Native_input_index_candidate_v1.json'
q['archive_inputs']['LQI']=dict(archive=records[0],sidecars=records[1:],prediction_index=rec(lqi_index),prediction_protocol=rec(B/'lqi_native_prediction_preparation_v1/LQI_CD_210_Native_prediction_scope_v1.json'),prediction_request_sha256='cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6')
q['evidence']=dict(formal_LQI_prediction_audit=rec(B/'lqi_native_prediction_implementation_v1/post_prediction_freeze_audit_v1/post_prediction_freeze_audit_result_v1.json'),formal_F0_prediction_audit=old['evidence']['formal_F0_prediction_audit'],local_archives_verified=rec(PRE/'local_LQI_and_F0_archive_verification_v1.json'),preparation_receipt=rec(PRE/'preparation_validation_receipt_v1.json'),baseline_compatibility_bindings=rec(PRE/'entry_compatibility_and_baseline_bindings_v1.json'),formal_F0_score_audit=gaps['frozen_F0_score_audit'],CPU_contracts=rec(cpu),P3=rec(S/'implementation_P3_v1.json'),frozen_scoring_protocol=rec(S/'frozen_scoring_protocol_v1.json'))
q['scientific_contract']=dict(arms=['F0','LQI'],controls=['Nop_D','GT_8192'],pairs=[['F0','LQI']],delta='LQI minus F0; error improvement negative, coverage improvement positive',primary='A1 area-weighted E_P95; mean five defects/source then21 sources equally/fold',geometry=old['scientific_contract']['geometry'],risk=old['scientific_contract']['risk'],alignment='Native world mm, no GT alignment/ICP/postfilter',coarse='All420 predictions have actual Q256 and P8192; complete same-case coarse diagnostics',baseline_archive_handling='Reuse frozen F0/LQI predictions; no re-inference; compare630 recomputed F0/control rows against frozen baseline values',diagnostic_cache='F0 retained20context10trace identity-bound not scored; LQI exact empty cache log and no contexts/traces')
q['future_authorization']=dict(path=str((S/'authorized_execution_v1/score_authorization_v1.json').resolve()),schema='bcsp-lqi-F0-score-authorization-v1')
q['invocation_contract']['readiness']='Rehash scorer/metric/evidence/2archives/sidecars/frozen baseline scores/CPU Python/210references/210points; actual output/control targets absent'
q['completion_boundary']='Separate formal read-only post-score freeze audit before LQI/F0 effect interpretation'
q['limits']=protocol['limits'];q['forbidden']=protocol['prohibited']
assert not Path(q['output']).exists() and not Path(q['future_authorization']['path']).parent.exists()
for r in q['evidence'].values():exact(r)
assert sha(entry)==p3['scorer']['sha256']
emit('local_scoring_execution_request_v1.json',q)
receipt=dict(status=q['status'],request=rec(S/'local_scoring_execution_request_v1.json'),P3=rec(S/'implementation_P3_v1.json'),counts=q['counts'],CPU_tests=50,execution_materialized=False,real_scoring_executed=False,requires_upload=False)
emit('request_preparation_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=True,indent=2))
