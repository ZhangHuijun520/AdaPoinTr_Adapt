"""Freeze tools,references and ONE pending inference scope. No server execution."""
import ast,hashlib,io,json,tarfile
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parent;ROOT=next(x for x in N.parents if x.name=='mamba-ccf-c-1-high-resolution')
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def bind(p):return dict(path=str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=digest(p))
def put(name,value):
 p=N/name
 with p.open('x',encoding='ascii') as f:json.dump(value,f,ensure_ascii=True,indent=2,allow_nan=False)
 return p
def check(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'];return p

refpath=N/'reference_bank_v2/reference_manifest_v1.json';refs=json.loads(refpath.read_bytes())
assert refs['status']=='FROZEN_210_CASE_A1_A2_B_REFERENCES' and len(refs['cases'])==210 and len({r['case_id'] for r in refs['cases']})==210
assert not refs['model_predictions_used'] and not (refpath.parent/'failure_v1.json').exists()
for r in refs['cases']:check(r)
index=json.loads((N/'development_input_index_v1.json').read_bytes());assert len(index['inputs'])==420 and len(index['runs'])==4
tests=[json.loads((N/x).read_bytes()) for x in ['geometry_CPU_contract_result_v1.json','prediction_score_CPU_result_v2.json','controller_CPU_result_v2.json']]
assert all(x['status']=='PASS' and x['failures']==x['errors']==0 for x in tests) and sum(x['tests'] for x in tests)==46
assert tests[0]['source_sha256']==digest(N/'bcsp_eval_metrics_v1.py')
for name,sha in tests[1]['implementation'].items():assert sha==digest(N/name)
assert tests[2]['source_sha256']==digest(N/'development_controller_template_v1.py')
ready=json.loads((N/'server_readiness_report_v2.json').read_bytes());assert ready['status']=='FOUR_MODEL_DEVELOPMENT_READINESS_PASS'
parent=json.loads((B/'foldD_16384_training_v1/training_entry_request_v1.json').read_bytes())
base='/home/jovyan/adapointr_work/PoinTr';code=base+'/third_party/bcsp_geov1_training_foldc_8192_seed0_v1';output=base+'/logs/cranial_bcsp_geov1/development_four_models_seed0_v1';control=code+'/control_eval_four_models_v1'
entry=bind(N/'bcsp_development_predict_v1.py');entry['path']=code+'/bcsp_development_predict_v1.py'
input_record=bind(N/'development_input_index_v1.json');input_record['path']=code+'/evidence/development_input_index_v1.json'
oldscope=json.loads((B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json').read_bytes())
environment=dict(oldscope['environment']);environment.update(CUDA_VISIBLE_DEVICES=parent['identity']['gpu_uuid'],TMPDIR='<owned_output>/tmp')
q=dict(schema='bcsp-four-model-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='bcsp_four_model_development_seed0_v1',
 identity=parent['identity'],model_root=parent['model_root'],entry=entry,input_index=input_record,fold_binding=parent['QC']['fold_binding'],static_config=parent['static_config'],
 preflight_scope=parent['preflight_scope'],helper=parent['implementation']['preflight_helper'],control=control,output=output,launch_attempt=control+'/launch_attempt.json',environment=environment,
 limits=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296),
 science=dict(models=4,forwards_per_model=105,total_forwards=420,unique_cases=210,unique_sources=42,seed=0,n_output=8192,training_updates=0,BNCal=False,loss=False,backward=False,
  precision='FP32',deterministic=True,TF32=False,mode='eval/inference_mode',checkpoint='scratch_final_epoch99_updates3900',state_invariance_required=True,
  loss_backend_during_parent_training='existing_torch_cdist;no loss called during inference',PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'))
qp=put('development_entry_request_v1.json',q)
mapping=[]
for name,target in [('bcsp_development_predict_v1.py',entry['path']),('development_input_index_v1.json',input_record['path'])]:
 r=bind(N/name);mapping.append(dict(member=name,target=target,bytes=r['bytes'],sha256=r['sha256']))
archive=N/'bcsp_four_model_development_eval_v1.tar.gz'
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  for r in mapping:
   data=(N/r['member']).read_bytes();m=tarfile.TarInfo(r['member']);m.size=len(data);m.mode=0o600;m.mtime=0;t.addfile(m,io.BytesIO(data))
for suffix,text in [('sha256',digest(archive)+'  '+archive.name+'\n'),('bytes',str(archive.stat().st_size)+'\n'),('contents.sha256',''.join(r['sha256']+'  '+r['member']+'\n' for r in mapping))]:
 with (N/(archive.name+'.'+suffix)).open('x') as f:f.write(text)
for name in ['bcsp_eval_metrics_v1.py','bcsp_development_predict_v1.py','bcsp_development_score_v1.py','development_controller_template_v1.py']:ast.parse((N/name).read_text())
protocol=ROOT/'docs/cranial_bcsp_geov1_20261024/four_model_development_evaluation_protocol_zh_v1.md'
note=ROOT/'docs/cranial_bcsp_geov1_20261024/four_model_development_evaluation_implementation_note_zh_v1.md'
source_files=['bcsp_eval_metrics_v1.py','bcsp_development_predict_v1.py','bcsp_development_score_v1.py','development_controller_template_v1.py','build_reference_bank_v2.py']
p3=put('local_P3_v1.json',dict(status='LOCAL_P3_PASS_FOR_PENDING_INFERENCE_SCOPE',test_count=46,
 tests=[bind(N/x) for x in ['geometry_CPU_contract_result_v1.json','prediction_score_CPU_result_v2.json','controller_CPU_result_v2.json']],
 implementation={x:bind(N/x) for x in source_files},reference_manifest=bind(refpath),reference_count=210,reference_bytes=refs['reference_bytes'],reference_model_predictions_used=False,
 index=bind(N/'development_input_index_v1.json'),entry_request=bind(qp),protocol=bind(protocol),implementation_note=bind(note),readiness=bind(N/'server_readiness_report_v2.json'),
 fixed_models=[dict(label=r['label'],checkpoint=r['checkpoint'],formal_freeze=r['freeze_audit']) for r in index['runs']],
 checks=dict(four_final_checkpoint_audits=True,source_folds_disjoint=True,shared_GT_and_nested_inputs_inherited_QC=True,exact_420_server_inputs_verified=True,
  reference_raw_hashes_verified_before_after=True,J_faces_and_area_match_prior_QC=True,metrics_fixed_before_predictions=True,eval_only_no_training_calls=True,
  one_way_authorization=True,exclusive_two_file_transport=True,fresh_control_and_output=True,CPU_contract_hashes_current=True),
 limits=['CPU tests do not validate real CUDA inference','Windows exclusive-write fixture emulates O_NOFOLLOW constant;not a Linux symlink race proof','Resource monitoring is sampled,not dedicated hard cgroup isolation','Only fixed seed0,OOF development,not independent final test','Actual downloaded archive must be hash-bound before local scoring;no real scoring done'],
 production_authorization_materialized=False,server_installs=0,model_forwards=0,training=0,BNCal=0))
upload=bind(archive);upload['path']='/home/jovyan/'+archive.name
reused=ready['files']+[dict(path='/opt/conda/envs/adapointr-mamba/bin/python3.10',bytes=17331920,sha256='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d')]
request=put('development_execution_request_v1.json',dict(schema='bcsp-four-model-development-execution-scope-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,
 date_Asia_Shanghai='2026-10-26',request_kind='Exclusive two-file deployment then ONE native420-forward four-model development prediction batch;local scoring separately authorized after verified download',
 entry_request=bind(qp),entry_request_future_server_path=control+'/entry_request.json',controller_template=bind(N/'development_controller_template_v1.py'),upload=upload,local_upload=bind(archive),install_mapping=mapping,
 tmux_session='bcsp_dev_four_models_seed0_v1',reused_assets=reused,protocol=bind(protocol),implementation_note=bind(note),local_P3=bind(p3),reference_manifest=bind(refpath),
 authorization_order=['Verify full outer SHA and explicit user grant','Recheck identity,upload,all targets absent,all fixed dependencies/inputs/checkpoints,GPU idle,disk','Exclusive install two files and readback hashes','Create fresh control/output','Write entry request -> authorization receipt -> its SHA -> runtime -> launcher -> single-use claim','One tmux launch only;observe session/exit receipt'],
 runtime_materialization_authorized_now=False,launcher_materialized_now=False,expected_output=output,
 result_archive_files=[output+'/development_predictions_v1.tar.gz'+suffix for suffix in ['', '.sha256','.bytes','.contents.sha256']],
 predictions=dict(models=4,cases_per_model=105,forwards=420,n_output=8192,warmup=0,voting=0,source_count=42,case_count=210),
 scoring=dict(status='NOT_EXECUTED_REQUIRES_VERIFIED_MANUAL_DOWNLOAD_AND_SEPARATE_SCOPE',tool=bind(N/'bcsp_development_score_v1.py'),primary='A1 area-weighted E_G_to_prediction P95 mm',paired_unit='source mean of5 defects',delta='16k minus8k',bootstrap=10000,seed=20261024),
 failed_attempt_policy='STOP;no retry,resume,automatic repair/relaunch,new training,BNCal,case selection or parameter scan',
 resource_limits=q['limits'],server_data_uploads=0,new_training=0,BNCal=0,GPU_predictions_run_now=0))
with (N/'development_execution_request_v1.json.sha256').open('x') as f:f.write(digest(request)+'  '+request.name+'\n')
result=put('preparation_completion_v1.json',dict(status='READY_AWAITING_EXPLICIT_USER_EXECUTION_AUTHORIZATION',protocol=bind(protocol),P3=bind(p3),request=bind(request),transport=bind(archive),reference_manifest=bind(refpath),tests=46,reference_cases=210,model_predictions=0,server_installs=0,training=0,BNCal=0))
print(json.dumps(dict(status='PENDING_FOUR_MODEL_EVALUATION_REQUEST_FROZEN',request_sha256=digest(request),transport_sha256=digest(archive),transport_bytes=archive.stat().st_size,references=210,tests=46,forwards_executed=0)))
