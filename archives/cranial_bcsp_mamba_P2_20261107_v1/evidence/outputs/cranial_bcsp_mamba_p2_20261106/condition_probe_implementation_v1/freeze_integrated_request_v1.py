"""Freeze CPU P3, exact index and pending request; no server operation/materialization."""
import ast,copy,hashlib,json
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];P1=R/'outputs/cranial_bcsp_mamba_p1_20261104';P2=S.parent
ROOT=PurePosixPath('/home/jovyan/adapointr_work/PoinTr');INSTALL=ROOT/'third_party/bcsp_p2_condition_probe_20261107_v1';OUT=ROOT/'logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1'
def bind(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def remote(p,dest=None):b=bind(p);b['path']=str(dest or INSTALL/Path(p).name);return b
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def emit(p,v):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
def hash_jsonl(binding):
 p=Path(binding['path']);assert bind(p)==binding;return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
first=read(S/'artificial_cpu_batch_v1/result_v1.json');integrated=read(S/'integration_cpu_result_v1.json')
assert first['status']=='ARTIFICIAL_CPU_CONTRACT_PASS' and integrated['status']=='ARTIFICIAL_FULL_INTEGRATION_PASS' and first['tests']==20 and integrated['tests']==8
assert integrated['failures']==integrated['errors']==first['failures']==first['errors']==0
for b in integrated['bindings']:assert bind(b['path'])==b
for n,h in first['source_sha256'].items():assert bind(S/n)['sha256']==h
assert bind(S/'artificial_cpu_batch_v1/stdout_v1.txt')['sha256']==first['stdout_sha256']
for n in ['condition_probe_entry_v1.py','condition_probe_core_v1.py','coarse_prefix_capture_v1.py']:ast.parse((S/n).read_text(encoding='utf-8'))
completed=read(S/'integration_cpu_batch_v1/complete/probe_complete.json');assert completed['prefixes']==1680 and len(completed['model_evidence'])==4 and all(r['prefix_calls']==420 and r['state_unchanged'] and r['RNG_unchanged'] for r in completed['model_evidence'])
manifest=[json.loads(x) for x in (S/'integration_cpu_batch_v1/complete/tensor_manifest.jsonl').read_text().splitlines()];assert len(manifest)==1680 and len({r['file']['name'] for r in manifest})==1680
for row in manifest:
 b=bind(S/'integration_cpu_batch_v1/complete'/row['file']['name']);assert (b['bytes'],b['sha256'])==(row['file']['bytes'],row['file']['sha256'])
failure=read(S/'integration_cpu_batch_v1/failure/failure.json');assert failure['status']=='FAILED_STOP_NO_RETRY' and failure['prefix_attempts']==0
basepath=P1/'paired_development_evaluator_v2/transport_payload/FoldC_T0_M0_development_execution_request_v2.json';base=read(basepath)
assert bind(P1/'paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py')['sha256']==base['entry']['sha256']
candidate=read(S/'local_candidate_assets_v1.json');uploads=read(S/'checkpoint_upload_verification_20261107_v1.json');assert uploads['status']=='READONLY_FOUR_CHECKPOINT_UPLOAD_VERIFICATION_PASS'
inputs={r['case_id']:r for r in candidate['unique_point_files']};qtrain=read(P1/'training_entry_v1/transport_payload/T0_foldC_seed0_training_execution_request_v1.json');dtrain=read(P1/'FoldD_pair_preparation_20261106_v1/frozen_FoldD_training_input_index_v1.json')
drows={r['case_id']:r for r in dtrain['inputs']}
scorebanks={};native={}
for fold,sub in [('C','paired_development_evaluator_v2'),('D','FoldD_paired_development_entry_v1')]:
 audit=read(P1/sub/'post_scoring_freeze_audit_v1/audit_report_v1.json');assert audit['status']=='FORMAL_POST_SCORING_FREEZE_AUDIT_PASS'
 binding=next(b for b in audit['output_manifest'] if Path(b['path']).name=='case_metrics.jsonl');scorebanks[fold]=bind(P1/sub/'post_scoring_freeze_audit_v1/audit_report_v1.json')
 for row in hash_jsonl(binding):
  if row['arm'] not in ['T0','M0']:continue
  n=inputs[row['case_id']]['normalization'];s=row['stage_geometry']['coarse'];native[fold+'_'+row['arm'],row['case_id']]=dict(centroid=[(x-c)/n['scale'] for x,c in zip(s['centroid_mm'],n['center'])],radius_gyration=s['radius_gyration_mm']/n['scale'])
index=dict(schema='bcsp-p2-condition-probe-input-index-v1',runs=[],inputs=[],provenance=dict(local_assets=bind(S/'local_candidate_assets_v1.json'),baseline_score_audits=scorebanks))
for run in candidate['runs']:
 label=run['label'];f=run['fold'];v=run['variant'];up=next(r for r in uploads['files'] if r['sha256']==run['local_checkpoint']['sha256']);rr={k:run[k] for k in ['label','fold','variant','train_case_ids','dev_case_ids']};rr.update(seed=0,checkpoint={k:up[k] for k in ['path','bytes','sha256']});index['runs'].append(rr)
 for role,ids in [('train',rr['train_case_ids']),('development',rr['dev_case_ids'])]:
  for cid in ids:
   src=inputs[cid];b=copy.deepcopy(src['local_input'])
   # Explicit old Linux root from frozen C training request or exact old D metadata.
   if (f=='C' and role=='train') or (f=='D' and role=='development'):b['path']=str(PurePosixPath(qtrain['data_root'])/'points'/(cid+'_8192.npz'))
   else:
    old=drows[cid];b['path']=old['input']['path'];assert b['sha256']==old['input']['sha256']
   row=dict(run=label,fold=f,variant=v,role=role,case_id=cid,source_id=src['source_id'],input=b,target_array_sha256=src['target_array_sha256'],normalization=src['normalization'],normalization_source=src['normalization_source'])
   if role=='development':row['frozen_coarse']=native[label,cid]
   index['inputs'].append(row)
emit(S/'condition_probe_input_index_v1.json',index)
spec=__import__('importlib.util',fromlist=['spec_from_file_location']);sp=spec.spec_from_file_location('index_static_check',S/'condition_probe_entry_v1.py');entry=spec.module_from_spec(sp);sp.loader.exec_module(entry);entry.validate_index(index)
p3=dict(status='LOCAL_CONDITION_PROBE_INTEGRATION_P3_PASS',entry_sha256=bind(S/'condition_probe_entry_v1.py')['sha256'],core_CPU_result=bind(S/'artificial_cpu_batch_v1/result_v1.json'),integration_CPU_result=bind(S/'integration_cpu_result_v1.json'),total_artificial_CPU_checks=28,full_artificial_four_model_prefixes=1680,full_artificial_tensor_files=1680,full_artificial_summaries=4,source_hashes_verified=True,static_AST_parse=True,production_index_contract_pass=True,checks=dict(real_head_capture_and_no_dense=True,exclusive_writer_and_manifest_hashes=True,actual_frozen_parent_checkpoint_loader_used_on_synthetic_weights=True,GT_only_after_D_only_prefix=True,no_backprop_optimizer_or_BNCal=True,training_only_normalization_ridge_lambda1=True,source_equal_and_fixed_defect_strata=True,resource_stop_and_failure_receipt=True,one_way_authorization_and_runtime=True,state_BN_RNG_preservation_artificial=True),limits=['Artificial CPU models are not production Mamba/CUDA verification','Production main bootstrap/provider/payload policy inherited and statically reviewed, not executed against real environment','Current resource observation and upload hashes are prior read-only evidence; exact source/provider/data/Python/driver identities must be rechecked before install/launch','Native coarse equivalence tolerance inherited and enforced on all105 dev cases/model; cross-device mismatch will stop, not loosen tolerance'],real_checkpoint_loads=0,real_data_array_reads=0,real_forward_calls=0,server_operations_this_implementation=0)
emit(S/'final_implementation_P3_v1.json',p3)
keys=['identity','environment','dependencies','implementation','numeric_policy','preflight_scope','static_config','helper','model_root','limits'];q={k:copy.deepcopy(base[k]) for k in keys}
q['identity'].update(hostname=uploads['hostname'],gpu_uuid='GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52');q['environment']['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid']
q.update(schema='bcsp-p2-condition-probe-execution-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,prefix_budget=1680,backward=0,optimizer_steps=0,dense_forwards=0,BNCal=0,entry=remote(S/'condition_probe_entry_v1.py'),capture=remote(S/'coarse_prefix_capture_v1.py'),core=remote(S/'condition_probe_core_v1.py'),parent_entry=base['entry'],input_index=remote(S/'condition_probe_input_index_v1.json'),P3=remote(S/'final_implementation_P3_v1.json'),output=str(OUT),launch_attempt=str(INSTALL/'control/launch_attempt_v1.json'))
q['launch_contract']=dict(tmux_session='bcsp_p2_condition_probe_CD_20261107_v1',request_path=str(INSTALL/'condition_probe_execution_request_v1.json'),authorization_path=str(INSTALL/'control/authorization_v1.json'),runtime_path=str(INSTALL/'control/runtime_v1.json'),launcher_path=str(INSTALL/'control/launch_once_v1.sh'),log=str(OUT/'launch.log'),PID=str(OUT/'worker.pid'),exit_code=str(OUT/'exit_code.txt'),materialization_order='authorization -> SHA256 -> runtime(one-way auth binding) -> launcher; exclusive claim before one tmux launch',parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='Original file bytes, no text decode/reencode',automatic_retry=False)
q['readiness_prerequisites']=['Fresh hostname/UID/UUID/idle<=256MiB/disk>=4GiB check','Rehash inherited exact source/provider/extensions/Python/driver; driver570.190 and Python3.10.20 are required inherited expectations, not newly verified observations','Rehash all420 unique input files at the exact per-role frozen server paths; reject source/fold or target mismatch','Rehash four uploaded weights, no copy/restore to old logs required','Every new install/control/output target must be absent; verify parents and no links, exclusive writes only','Use external timeout7200s inherited from P1 (same RSS8GiB/torch20GiB/device22528MiB/output1GiB); conservative cap, not a performance guarantee','Verify no prior claim/session; failure consumes attempt, never auto-retry/resume']
q['scientific_contract']=dict(models=list(entry.MODEL_SHA),train_cases_per_model=315,development_cases_per_model=105,features='coarse_pred input1024; original Q256 output, stop before FPS/query/decoder',target='GT8192 empirical centroid3 + log radius in D-only frame',coarse_equivalence=dict(rtol_centroid=1e-9,rtol_radius=1e-8,atol=1e-7,policy='Inherited P1 saved Q vs summary, no tolerance adaptation'),geometry18='mean3 + covariance upper6 + axis quantiles.1/.5/.9 linear9',ridge='train-source-equal mean residual objective +1.0||W||^2; train-only X/Y standardization, unpenalized intercept',output_metrics=['centroid_mm','centroid_over_GT_radius','absolute_log_radius_error'],aggregation='mean5 defects/source then mean21 sources, per fold/model; all cases retained',CPU_readout_included=True,H2_selected=False,bootstrap=0,formal_gate=False)
q['not_authorized']=['Execution before separate full request hash authorization','Training/BNCal/weight changes/dense predictions','New cases/seeds/regularization scan or H2 model selection','Download/install/build/upgrade dependencies','Repeated GPU preflight','GT-conditioned model prefix','Automatic retry/resume or tolerance relaxation']
q['provenance']=dict(parent_request=bind(basepath),upload_verification=bind(S/'checkpoint_upload_verification_20261107_v1.json'),resource_observation=bind(S/'bounded_server_observation_v1.json'),CPU_core_20_plus_integration8=True,server_current_sources_not_reverified_in_implementation_only=True,limits_inherited=True,finite_backward_nondeterminism_disclosed_no_backward_this_execution=True)
emit(S/'condition_probe_execution_request_v1.json',q)
mapping=[]
for name in ['condition_probe_entry_v1.py','coarse_prefix_capture_v1.py','condition_probe_core_v1.py','condition_probe_input_index_v1.json','final_implementation_P3_v1.json','condition_probe_execution_request_v1.json']:
 mapping.append(dict(local=bind(S/name),target=str(INSTALL/name),overwrite=False))
emit(S/'pending_installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED',files=mapping,checkpoint_paths_reused_from_upload=True,prerequisites=q['readiness_prerequisites']))
print(json.dumps(dict(status=p3['status'],artificial_tests=28,input_rows=len(index['inputs']),request=bind(S/'condition_probe_execution_request_v1.json'),install_files=len(mapping),server_operations=0)))
