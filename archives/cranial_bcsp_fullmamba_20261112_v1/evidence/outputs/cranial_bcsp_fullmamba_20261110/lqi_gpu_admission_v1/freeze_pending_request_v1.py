"""Freeze local CUDA entry/P3 and pending transport; does not execute or deploy."""
import ast,hashlib,importlib.util,json,shutil,tarfile
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent;R=S.parents[2]
PROJECT='/home/jovyan/adapointr_work/PoinTr';REMOTE=PROJECT+'/third_party/bcsp_lqi_cuda_20261111_v1';RUN='LQI_artificial_cuda_20261111_v1'
def rec(p,path=None):return dict(path=path or str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())
def emit(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def module(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 entry=S/'bcsp_lqi_cuda_admission_v1.py';test=S/'test_lqi_cuda_entry_cpu_v1.py';e=module('lqi_entry_static_freeze',entry)
 cpu=read(S/'artificial_cpu_entry_batch_v1/result.json');implementation=B/'lqi_implementation_v1';ip3=read(implementation/'post_implementation_P3_v1.json')
 assert cpu['status']=='LQI_CUDA_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==29 and cpu['entry']==rec(entry) and cpu['test']==rec(test)
 assert ip3['status']=='F0_LQI_LOCAL_IMPLEMENTATION_ONLY_P3_PASS' and ip3['CPU_assertions']==55 and all(ip3['checks'].values())
 assert not (S/'artificial_cpu_entry_batch_v1/failure.json').exists()
 for r in ip3['sources']:assert rec(Path(r['path']))==r
 for k,n in [('lqi_decoder','bcsp_lqi_decoder_v1.py'),('lqi_factory','bcsp_lqi_factory_v1.py')]:assert cpu['implementation'][k]==rec(implementation/n)
 static_sources=[]
 for p in [entry,test,Path(__file__),S/'readiness_readonly_v1.py']:
  compile(ast.parse(p.read_text(encoding='utf-8')),str(p),'exec');static_sources.append(rec(p))
 tree=ast.parse(entry.read_text(encoding='utf-8'));assert not any(isinstance(n,ast.FunctionDef) and n.name=='decoder_checks' for n in tree.body)
 assert e.SCIENCE['full_forward']==e.SCIENCE['full_backward']==e.SCIENCE['full_loss']==2 and e.SCIENCE['full_batches']==[1,8]
 assert all(e.SCIENCE[k]==0 for k in ('decoder_forward','decoder_backward','optimizer_steps','real_data_reads','checkpoint_loads'))
 identity=read(S/'readiness_v1/identity_result_v1.json');assets=read(S/'readiness_v1/assets_result_v1.json')
 assert identity['status']=='LQI_CURRENT_IDENTITY_RESOURCE_TARGETS_PASS' and identity['new_targets_absent'] and assets['status']=='LQI_INHERITED_EXACT_ASSETS_PASS'
 emit(S/'entry_P3_v1.json',dict(status='LQI_CUDA_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],decoder_sha256=rec(implementation/'bcsp_lqi_decoder_v1.py')['sha256'],factory_sha256=rec(implementation/'bcsp_lqi_factory_v1.py')['sha256'],
  checks=dict(actual_authorize_contract_CPU=True,count_and_resource_fixture_drift_denied=True,exact2F2loss2B_CPU_fixture=True,eval_B1_trainmode_B8=True,all35_gradient_module_coverage_CPU=True,state_RNG_modes_restored_on_success_and_failure=True,first_failure_stops_no_retry=True,launcher_POSIX_parent_before_redirect=True,one_way_authorization_runtime=True,actual4_candidate_sources_loaded_under_finite_policy=True,no_frozenF0_dispatch_substitution=True,final55_assertion_LQI_implementation_identity=True,no_old_prefix_mechanism_or_extra_diagnostic=True,no_optimizer_creation_or_steps=True,native72_forward_SSM_budget_pinned=True,no_gradient_bitwise_equality_requirement=True,current_identity_and_exact_inherited_assets_readonly_verified=True),
  evidence=[rec(S/'artificial_cpu_entry_batch_v1/result.json'),rec(implementation/'post_implementation_P3_v1.json'),rec(S/'readiness_v1/identity_result_v1.json'),rec(S/'readiness_v1/assets_result_v1.json')],static_sources=static_sources,CPU_entry_assertions=29,CPU_implementation_assertions=55,CUDA_calls=0,server_writes=0,limitations=['Entry control-flow/backward tested on cheap artificial CPU loss; nativeMamba, provider and production loss await CUDA execution.','LQI formula CPU surrogate tests do not certify actual CUDA performance or scientific efficacy.'],next_gate='Separate exact request-hash authorization; single execution then independent formal post-CUDA freeze audit; no automatic training.'))
 T=S/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
 sourcefiles=[entry,implementation/'bcsp_lqi_decoder_v1.py',implementation/'bcsp_lqi_factory_v1.py',S/'entry_P3_v1.json',implementation/'post_implementation_P3_v1.json',S/'artificial_cpu_entry_batch_v1/result.json',B/'query_aligned_condition_spec_v1/formula_interface_freeze_v1.json']
 for p in sourcefiles:shutil.copyfile(p,P/('entry_CPU_result_v1.json' if p.name=='result.json' else p.name))
 parent=read(B/'conditional_diagnostic_implementation_v1/frozen_pending_transport_v1/payload/F0_CD_decoder_diagnostic_execution_request_v1.json')
 old=read(B/'gpu_admission_v1/F0_artificial_cuda_execution_request_v1.json')
 I=dict(parent['identity']);assert I['hostname']==identity['hostname'] and I['python_realpath']==identity['python_realpath'] and I['python_version']==identity['python_version']
 assert identity['GPU'][:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])]
 q=dict(schema='bcsp-lqi-synthetic-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,date='2026-11-11',candidate='F0-LQI-v1',run_id=RUN,identity=I,project=PROJECT,
  environment=parent['environment'],model_root=parent['model_root'],dependencies=parent['dependencies'],helper=parent['helper'],parent_helper=parent['native_helper'],preflight_scope=parent['preflight_scope'],static_config=parent['static_config'],timezone_implementation=parent['implementation']['timezone'],timezone_resource=old['timezone_resource'],
  implementation=dict(encoder=parent['implementation']['encoder'],factory=parent['implementation']['factory'],lqi_decoder=rec(implementation/'bcsp_lqi_decoder_v1.py',REMOTE+'/bcsp_lqi_decoder_v1.py'),lqi_factory=rec(implementation/'bcsp_lqi_factory_v1.py',REMOTE+'/bcsp_lqi_factory_v1.py')),
  entry=rec(entry,REMOTE+'/'+entry.name),P3=rec(S/'entry_P3_v1.json',REMOTE+'/entry_P3_v1.json'),implementation_P3=rec(implementation/'post_implementation_P3_v1.json',REMOTE+'/post_implementation_P3_v1.json'),CPU_entry_result=rec(P/'entry_CPU_result_v1.json',REMOTE+'/entry_CPU_result_v1.json'),formula_specification=rec(B/'query_aligned_condition_spec_v1/formula_interface_freeze_v1.json',REMOTE+'/formula_interface_freeze_v1.json'),
  science=e.SCIENCE,tolerances=e.TOLERANCE,limits=e.LIMITS,fixture=e.FIXTURE,output=PROJECT+'/logs/cranial_bcsp_fullmamba/'+RUN,
  readiness=dict(identity_verified=True,inherited_assets_verified=True,local_identity_evidence=rec(S/'readiness_v1/identity_result_v1.json'),local_assets_evidence=rec(S/'readiness_v1/assets_result_v1.json'),reverify_immediately_before_launch=True,local_paths_are_provenance_only=True),
  numeric=dict(FP32=True,TF32=False,strict_deterministic=True,finite_gradient_nondeterminism_accepted=True,bitwise_gradient_repeat_required=False,loss_backend='existing_PyTorch_cdist_Chamfer_only_no_compiled_Chamfer',PointNet2_backend='exact_existing_Python310_native_provider',no_mixed_precision=True),
  required_gradient_prefixes='35 module groups: coarse,PE,reduce_map,6encoder_mixers,16decoder_mixers,8norm_v,increase_dim,decode_head; all present gradients finite; each group nonzero',
  restoration='After each phase and on failure restore full state_dict including BN buffers, gradients cleared, RNG(Python NumPy CPU CUDA), module training flags and BN momenta; no optimizer instantiated.',
  counters='2 whole-model forwards;2 complete original loss calls;2 backwards;72 forward nativeSSM hooks(6encoder*4+8decoder_self*4+8decoder_cond*2). No separate decoder forwards, repeats, diagnostics or warmup.',
  resource_policy=dict(RSS='8GiB monitored, no exclusive hard cgroup guarantee',torch_peak='20GiB allocated/reserved',physical_GPU_stop_MiB=22528,initial_GPU_max_MiB=256,monitoring_poll_seconds=2,nvidia_smi_timeout_seconds=10,nvidia_smi_no_retry=True,PID='diagnostic only, no host-procfs ownership assertion',wall_budget_reason='inherit fixed1800s, reduced to2 complete loss/backward phases including B8; not a performance claim'),
  forbidden=['Execution before separate fullSHA authorization','optimizer construction/step; training run; real data or checkpoint reads; BNCal; evaluation','download/build/install/upgrade dependencies','extra forward/backward/warmup/old prefix intervention; retry or resume','change model/source/fixture/loss/provider/resource thresholds','automatic training admission'],
  required_outputs=['worker.pid','events.jsonl','resources.jsonl','construction.json','completion.json OR failure.json/monitor_failure.json','payload_manifest.json on success','launch.log','exit_code.txt'],
  post_execution_formal_freeze_audit_required=True,scientific_efficacy='NOT_TESTED_BY_SYNTHETIC_ADMISSION')
 q['launch_contract']=dict(tmux_session='bcsp_lqi_cuda_20261111_v1',request_path=REMOTE+'/LQI_artificial_cuda_execution_request_v1.json',authorization_path=REMOTE+'/control/authorization_v1.json',runtime_path=REMOTE+'/control/runtime_v1.json',launcher_path=REMOTE+'/control/launch_once_v1.sh',launch_attempt_path=REMOTE+'/control/launch_attempt_v1.json',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt',materialization_order='authorization -> SHA256 -> runtime(one-way) -> launcher -> one claim -> one tmux attempt',parent_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True,transport='original bytes only; raw byte response capture',exclusive_single_attempt=True,automatic_retry=False,timeout_kill_after_seconds=10)
 qp=P/'LQI_artificial_cuda_execution_request_v1.json';emit(qp,q);qh=rec(qp)['sha256']
 # Complete pending-request contract review with an in-memory artificial authorization ONLY.
 artificial_auth=dict(schema='bcsp-lqi-cuda-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='LOCAL_STATIC_REVIEW_ONLY_NOT_EXECUTION_AUTHORIZATION')
 e.authorize(q,qh,artificial_auth,'a'*64,dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256=qh,authorization_sha256='a'*64))
 launcher=e.render_launcher(q,qh,'a'*64,'b'*64);assert q['entry']['path'] in launcher and '\\' not in launcher.replace('\\n','')
 emit(S/'final_contract_review_v1.json',dict(status='FINAL_PENDING_REQUEST_CONTRACT_PASS',request=rec(qp),entry=rec(entry),launcher_only_rendered_in_memory=True,launcher_materialized=False,actual_authorization_materialized=False,science=q['science'],full_runtime_authorization_contract_checked=True,model_source_after_CPU_unchanged=True,readiness_files=assets['files'],readiness_hashed_bytes=assets['hashed_bytes'],server_writes=0,CUDA_calls=0))
 files=[dict(member='payload/'+p.name,target=REMOTE+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())]
 assert len(files)==8
 mapping=dict(status='FROZEN_PENDING_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',remote_root=REMOTE,request_sha256=qh,files=files,reused_readonly_files='request helper/parent_helper/scope/static/timezone/encoder/factory/dependencies + exactscope provider/project sources',
  before_write='reverify identity/GPU/disk, exact archive+3 sidecars, every8 target and new root/control/output absent, no symlink ancestors; exclusive creation only',
  not_materialized=[q['launch_contract'][k] for k in ('authorization_path','runtime_path','launcher_path','launch_attempt_path')]+[q['output']],failure='stop immediately, preserve receipts, no automatic retry or resume')
 emit(T/'installation_mapping_v1.json',mapping);arc=T/'bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz'
 with arc.open('xb') as f:
  with tarfile.open(fileobj=f,mode='w:gz') as tar:
   tar.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
   for p in sorted(P.iterdir()):tar.add(p,arcname='payload/'+p.name,recursive=False)
 with tarfile.open(arc,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==9 and all(m.isfile() and m.size<1048576 for m in members)
  listing=''.join(hashlib.sha256(tar.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
 for suffix,value in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
  with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(value)
 emit(S/'delivery_receipt_v1.json',dict(status='AWAITING_MANUAL_UPLOAD_AND_SEPARATE_EXACT_HASH_EXECUTION_AUTHORIZATION',request=rec(qp),archive=rec(arc),install_files=8,archive_members=9,entry_P3=rec(S/'entry_P3_v1.json'),CPU_assertions=29,server_writes=0,CUDA_calls=0,training_request_created=False))
 print(json.dumps(dict(status='PENDING_REQUEST_FROZEN',request_SHA256=qh,archive_SHA256=rec(arc)['sha256'],archive_bytes=arc.stat().st_size),indent=2))
if __name__=='__main__':main()
