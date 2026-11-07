"""Local P3/protocol/request freeze only. No actual scoring or authorization materialization."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];P2=HERE.parent
PREP=P2/'H1_local_score_preparation_20261107_v1'
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def read(p):return json.loads(p.read_bytes())
def emit(n,x):
 with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
resultpath=HERE/'artificial_cpu_batch_v1/result_v1.json';result=read(resultpath)
assert result['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==32
assert not (HERE/'artificial_cpu_batch_v1/failure_v1.json').exists()
static=read(HERE/'static_review_v1.json')
for r in static['files']:assert sha(HERE/r['name'])==r['sha256']
scorer=HERE/'bcsp_p2_h1_M0_twofold_score_v1.py'
metric=ROOT/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
assert sha(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
parent=P1/'paired_development_evaluator_v2/scoring_implementation_v1/bcsp_p1_pair_score_v1.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
A=nodes(parent);B=nodes(scorer);inherited=['load_prediction_arrays','load_prediction','select_metrics','position_shape','risk_labels','stage_geometry','csv_rows']
assert all(A[n]==B[n] for n in inherited)
p3=dict(status='LOCAL_H1_M0_TWOFOLD_SCORING_P3_PASS',scorer=rec(scorer),test=rec(HERE/'test_h1_M0_score_cpu_v1.py'),CPU_result=rec(resultpath),CPU_tests=32,
 static_review=rec(HERE/'static_review_v1.json'),metric=rec(metric),parent=rec(parent),unchanged_AST_functions=inherited,
 review_checks=dict(three_archive_routes_H1_baselineC_baselineD=True,perfold_reference_and_model_pairing=True,exact840case168source_rows=True,
   H1_minus_M0_direction_correct=True,source_equal_5defects21sources_eachfold=True,perfold_risk_new_rescued_cases=True,
   finite_schema_checkpoint_input_hash_and_state_RNG_archive_validation=True,metric_core_and_numeric_thresholds_unchanged=True,
   missing_binding_or_case_failure_stops_no_drop=True,no_GPUTorch_model_or_checkpoint_import=True,backup_readonly=True),
 real_score_rows=0,artificial_actual_metric_rows=8,artificial_orchestrated_rows=840,
 limits=['840-row integration uses two analytic-case metric templates; actual geometry arithmetic tested on8 synthetic rows',
 'No real prediction/reference/input arrays decoded in implementation/tests','No research score or formal gate computed'],
 server_operations=0,real_scoring_executed=False,authorization_materialized=False)
emit('implementation_P3_v1.json',p3)
verificationpath=PREP/'local_archive_and_pair_verification_v1.json';verification=read(verificationpath)
assert verification['status']=='LOCAL_H1_AND_BASELINE_ARCHIVES_REFERENCE_PAIR_PASS'
casepath=PREP/'H1_M0_twofold_score_case_index_candidate_v1.json';caseindex=read(casepath)
assert len(caseindex['cases'])==210
refs=[]
for c in caseindex['cases']:
 refs.append(dict(case_id=c['case_id'],source_id=c['source_id'],fold=c['fold'],normalization=c['normalization'],target_array_sha256=c['target_array_sha256'],**c['reference']))
emit('reference_manifest_C_D_v1.json',dict(status='FROZEN_EXISTING_CD_210_REFERENCES',cases=refs,provenance=rec(casepath)))
protocol=read(PREP/'unified_CPU_scoring_protocol_candidate_v1.json')
protocol['status']='FROZEN_PENDING_SEPARATE_SCORING_EXECUTION_AUTHORIZATION'
protocol['schema']='bcsp-p2-H1-M0-twofold-local-scoring-protocol-v1'
emit('frozen_scoring_protocol_v1.json',protocol)
H=P2/'H1_prediction_implementation_v1'
specs={}
specs['H1']=dict(archive=verification['H1']['archive'],sidecars=verification['H1']['files'][1:],
 prediction_index=rec(H/'H1_C_D_input_index_v1.json'),prediction_protocol=rec(H/'H1_C_D_prediction_protocol_v1.json'),prediction_request_sha256='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147',fold='C_D')
for fold,sub in [('C','paired_development_evaluator_v2'),('D','FoldD_paired_development_entry_v1')]:
 D=P1/sub/'transport_payload';a=read(P1/sub/'post_prediction_freeze_audit_v1/audit_report_v1.json');v=verification['baselines'][fold]
 specs[fold]=dict(archive=v['archive'],sidecars=v['files'][1:],prediction_index=rec(D/'paired_development_input_index_v1.json'),prediction_protocol=rec(D/'paired_development_protocol_v1.json'),prediction_request_sha256=a['request_sha256'],fold=fold)
# Reuse the CPU environment actually used by the successful tests, resolving relocated path.
python=Path('C:/Users/zhj/.conda/envs/adapointr/python.exe').resolve()
oldenv=read(P1/'paired_development_evaluator_v2/scoring_implementation_v1/local_scoring_execution_request_v1.json')['environment']
assert rec(python)['sha256']==oldenv['python']['sha256'] and result['packages']==oldenv['packages']
counts=dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168)
out=HERE/'unified_scores_v1';auth=HERE/'authorized_execution_v1/score_authorization_v1.json'
assert not out.exists() and not auth.parent.exists()
q=dict(schema='bcsp-p2-H1-M0-twofold-local-scoring-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date_Asia_Shanghai='2026-11-07',
 purpose='Frozen H1 vs M0 Native paired CPU scores, C105+D105; no new inference',authorized_attempts_after_separate_full_hash_grant=1,
 implementation=dict(scorer=rec(scorer),metrics=rec(metric)),environment=dict(python=rec(python),python_version=result['python'],flags=['-I','-B'],packages=result['packages'],CUDA_VISIBLE_DEVICES='',threads=2),
 archive_inputs=specs,reference_manifest=rec(HERE/'reference_manifest_C_D_v1.json'),prediction_index=rec(H/'H1_C_D_input_index_v1.json'),score_case_index=rec(casepath),
 evidence=dict(formal_H1_prediction_audit=rec(H/'post_prediction_freeze_audit_20261107_v1/audit_report_v1.json'),
   formal_P1_C_prediction_audit=rec(P1/'paired_development_evaluator_v2/post_prediction_freeze_audit_v1/audit_report_v1.json'),
   formal_P1_D_prediction_audit=rec(P1/'FoldD_paired_development_entry_v1/post_prediction_freeze_audit_v1/audit_report_v1.json'),
   local_download_and_pair_verification=rec(verificationpath),CPU_contracts=rec(resultpath),P3=rec(HERE/'implementation_P3_v1.json'),frozen_scoring_protocol=rec(HERE/'frozen_scoring_protocol_v1.json')),
 P3=rec(HERE/'implementation_P3_v1.json'),output=str(out.absolute()),counts=counts,
 scientific_contract=dict(arms=['M0','M_H1'],controls=['Nop_D','GT_8192'],paired_delta='M_H1_minus_M0',perfold105=True,source_equal=True,
   primary='A1 area-weighted E_P95, mean5defects/source then21sources/fold',geometry='Same frozen E/J/CD/reverseA2/coarse-dense geometry and risk thresholds',
   risk='Report per-fold new/rescued/shared/neither; no filtering',alignment='Native world-mm only, no ICP/GT Oracle'),
 statistics=dict(bootstrap=0,p_values=False,formal_gate=False,perfold_report=True,seed0_only=True),limits=protocol['limits'],
 future_authorization=dict(path=str(auth.absolute()),schema='bcsp-p2-H1-M0-score-authorization-v1'),
 invocation_contract=dict(external_wall_timeout_seconds=14430,readiness='Rehash implementation, evidence, three archives/sidecars, fixed Python,210reference210point files; output/control paths absent',
   environment=dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'),
   claim='Exclusive authorization and process-attempt receipt before unique subprocess; no automatic retry/resume'),
 expected_result_files=['single_attempt_claim.json','execution_environment.json','case_metrics.jsonl','case_metrics.csv','source_metrics.json','source_metrics.csv','paired_comparison.json','paired_case_deltas.csv','defect_comparison.json','regression_rankings.json','risk_transitions.json','completion.json'],
 failed_attempt_policy='Fail whole batch; retain all partial logs; no dropped cases/retry/resume',completion_boundary='Completion is pending formal read-only score freeze audit; interpret effects only afterwards',
 forbidden=protocol['prohibited'],execution_materialized_now=False,real_scoring_executed_now=False)
emit('local_scoring_execution_request_v1.json',q)
receipt=dict(status=q['status'],request=rec(HERE/'local_scoring_execution_request_v1.json'),P3=rec(HERE/'implementation_P3_v1.json'),counts=counts,execution_materialized=False,real_scoring_executed=False)
emit('request_preparation_receipt_v1.json',receipt)
print(json.dumps(dict(status=q['status'],request_sha256=receipt['request']['sha256'],CPU_tests=32,case_score_rows=840,source_score_rows=168,scoring_executed=False)))
