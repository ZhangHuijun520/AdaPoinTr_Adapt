"""Local P3/pending scoring request. No real scores or authorized runtime materialization."""
import ast,hashlib,importlib.util,json
from pathlib import Path
S=Path(__file__).resolve().parent;R=S.parents[2];PRE=S.parent/'Native_prediction_implementation_v1/local_download_and_score_preparation_v1';AF=S.parent/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def read(p):return json.loads(p.read_bytes())
def exact(r):
 p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def emit(n,v):
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
entry=S/'bcsp_f0_T0_M0_three_arm_score_v1.py';test=S/'test_f0_three_arm_score_cpu_v1.py';cpu=S/'artificial_cpu_batch_v1/result_v1.json';result=read(cpu)
assert result['status']=='F0_T0_M0_SCORING_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==42 and result['real_score_rows']==0 and result['synthetic_actual_metric_rows']==15 and result['synthetic_orchestrated_rows']==1050 and not (cpu.parent/'failure_v1.json').exists()
for r in result['source_bindings']:exact(r)
static=read(S/'static_review_v1.json');assert static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
for r in static['files']:assert sha(S/r['name'])==r['sha256']
parent=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/bcsp_p2_h2_M0_three_arm_score_v1.py';metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
def funcs(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
old,new=funcs(parent),funcs(entry);keep=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','aggregate_source','describe_pairs','paired_summary','case_differences','defect_summary','csv_rows','risk_transitions']
assert all(ast.dump(old[n],include_attributes=False)==ast.dump(new[n],include_attributes=False) for n in keep)
class RemoveH2(ast.NodeTransformer):
 def visit_If(self,node):
  if ast.unparse(node.test)=="arm.startswith('H2_')":return None
  return self.generic_visit(node)
assert ast.dump(RemoveH2().visit(old['score_case']),include_attributes=False)==ast.dump(new['score_case'],include_attributes=False)
assert sha(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
indexpath=PRE/'F0_T0_M0_score_case_index_candidate_v1.json';index=read(indexpath);prep=read(PRE/'score_preparation_receipt_v1.json');verification=PRE/'local_archive_restore_verification_v1.json'
assert prep['status']=='LOCAL_RESTORE_VERIFIED_SCORE_SCOPE_PREPARED_IMPLEMENTATION_REQUIRED' and read(verification)['status']=='LOCAL_F0_FOUR_FILES_246_MEMBER_RESTORE_VERIFICATION_PASS'
assert len(index['cases'])==210 and len(index['prediction_records'])==630 and prep['real_scores_computed']==0
protocol=read(PRE/'F0_T0_M0_scoring_protocol_candidate_v1.json');assert protocol['counts']==index['counts'] and protocol['limits']==dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2)
protocol.update(schema='bcsp-f0-T0-M0-three-arm-local-scoring-protocol-v1',status='FROZEN_PENDING_SEPARATE_SCORING_EXECUTION_AUTHORIZATION');emit('frozen_scoring_protocol_v1.json',protocol)
refs=[dict(case_id=c['case_id'],source_id=c['source_id'],fold=c['fold'],normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],**c['reference']) for c in index['cases']]
emit('reference_manifest_C_D_v1.json',dict(status='FROZEN_EXISTING_210_REFERENCES_UNCHANGED',cases=refs,source=rec(indexpath)))
checks=dict(final_scorer_test_bytes_match_CPU_static=True,actual_frozen_index_reference_metadata_validated=True,three_archive_loaders_include_T0_M0_F0=True,F0_exact246_cache_trace_members_not_scored=True,all630_prediction_member_bindings_before_scoring=True,strict_F0_all_Q_and_baseline_optional_Q=True,metric_risk_source_and_pair_AST_unchanged=True,score_case_only_H2_specific_branch_removed=True,exact1050_rows420_shared_controls210_source_groups=True,correct_F0_M0_T0_pair_directions=True,new_and_rescued_risks_not_netted_away=True,undefined_pairs_retained_no_case_drop=True,source_equal_and_all_five_defects_kept=True,actual_authorize_and_negative_contracts_tested=True,fail_firstcase_no_false_completion=True,backup_no_extraction_or_write_in_entry=True,no_Torch_GPU_network_process_or_training_imports=True,CPU_metric_source_unchanged=True)
p3=dict(status='LOCAL_F0_T0_M0_SCORING_P3_PASS',date='2026-11-11',scorer=rec(entry),test=rec(test),CPU_result=rec(cpu),CPU_tests=42,static_review=rec(S/'static_review_v1.json'),parent=rec(parent),metric=rec(metric),unchanged_AST_functions=keep,checks=checks,real_score_rows=0,synthetic_actual_metric_rows=15,synthetic_orchestrated_rows=1050,server_operations=0,GPU_calls=0,limitations=result['limitations']+['Actual full process readiness and real1050-case scores await separate exact-hash execution authorization','Actual baseline Q only12 cases/arm, preserve missing values and restrict tensor-paired claims','Source-equal exploratory single-seed comparisons, no bootstrap/pvalue/gate'])
emit('implementation_P3_v1.json',p3)
oldplan=read(R/'outputs/cranial_bcsp_mamba_p2_20261106/H1_scoring_implementation_20261107_v1/local_scoring_execution_request_v1.json')
env=oldplan['environment'];exact(env['python']);assert result['packages']==env['packages'] and result['python']==env['python_version']
out=S/'unified_scores_v1';auth=S/'authorized_execution_v1/score_authorization_v1.json';assert not out.exists() and not auth.parent.exists()
evidence=dict(formal_F0_prediction_audit=rec(AF/'post_prediction_freeze_audit_result_v1.json'),local_F0_archive_verification=rec(verification),scoring_preparation_receipt=rec(PRE/'score_preparation_receipt_v1.json'),CPU_contracts=rec(cpu),P3=rec(S/'implementation_P3_v1.json'),frozen_scoring_protocol=rec(S/'frozen_scoring_protocol_v1.json'))
for k in ['formal_P1_C_prediction_audit','formal_P1_D_prediction_audit']:exact(oldplan['evidence'][k]);evidence[k]=oldplan['evidence'][k]
q=dict(schema='bcsp-f0-T0-M0-three-arm-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-11',purpose='Frozen Native F0/T0/M0 twofold paired CPU scores; no new inference or intervention',authorized_attempts_after_separate_full_hash_grant=1,implementation=dict(scorer=rec(entry),metrics=rec(metric)),environment=env,archive_inputs=index['archive_inputs'],reference_manifest=rec(S/'reference_manifest_C_D_v1.json'),prediction_index=index['archive_inputs']['F0']['prediction_index'],score_case_index=rec(indexpath),evidence=evidence,P3=rec(S/'implementation_P3_v1.json'),output=str(out.absolute()),counts=index['counts'],scientific_contract=dict(arms=['T0','M0','F0'],controls=['Nop_D','GT_8192'],pairs=[['M0','F0'],['T0','F0'],['T0','M0']],delta='candidate minus baseline for each fixed pair',primary='A1 area-weighted E_P95; mean5defects/source then21sources equally/fold',geometry='Exact inherited E/J/CD/Cover/reverseA2/position/radius/coarse-dense metrics and risk thresholds',risk='Per fold/case/source/defect; separate new/rescued and shared states derived from case labels; no filtering',alignment='Native world mm, no GT alignment/ICP/postfilter',coarse='F0 all210Q; T0/M0 each12Q: common-subset tensor comparison only, all-case existing summaries retained',baseline_archive_handling='Reuse bothT0/M0 frozen predictions; no re-inference',diagnostic_cache='20context10trace entries identity-bound but not scored as extra model outputs'),statistics=dict(bootstrap=0,p_values=False,formal_gate=False,perfold_report=True,seed0_only=True),limits=protocol['limits'],future_authorization=dict(path=str(auth.absolute()),schema='bcsp-f0-T0-M0-score-authorization-v1'),invocation_contract=dict(external_wall_timeout_seconds=18030,readiness='Rehash scorer/metric/evidence/3archives/sidecars/CPU Python/210references/210points; actual output/control targets absent',environment=dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),claim='Exclusive authorization and process-attempt receipt before unique subprocess; no automatic retry/resume'),expected_result_files=oldplan['expected_result_files'],failed_attempt_policy='Fail whole batch, retain partial evidence; no dropped cases, retry or resume',completion_boundary='Separate formal read-only post-score freeze audit before effect interpretation',forbidden=protocol['prohibited'],execution_materialized_now=False,real_scoring_executed_now=False)
emit('local_scoring_execution_request_v1.json',q)
receipt=dict(status=q['status'],request=rec(S/'local_scoring_execution_request_v1.json'),P3=rec(S/'implementation_P3_v1.json'),counts=index['counts'],CPU_tests=42,execution_materialized=False,real_scoring_executed=False,requires_upload=False)
emit('request_preparation_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
