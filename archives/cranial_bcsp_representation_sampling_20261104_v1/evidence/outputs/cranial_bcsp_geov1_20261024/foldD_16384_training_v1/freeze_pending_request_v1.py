from pathlib import Path
import copy,hashlib,io,json,tarfile
N=Path(__file__).resolve().parent;B=N.parent;D=B/'foldD_8192_training_v1';I=N/'implementation_v1'
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def bind(p,server=None):
 r=dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=sha(raw(p)))
 if server:r['future_server_path']=server
 return r
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p
results=load(I/'cpu_contract_v1/results_v1.json');assert results['status']=='PASS_15_FULL_AUTHORIZE_CPU_CONTRACTS'
audit_path=D/'freeze_audit_v1/audit_report_v1.json';audit=load(audit_path)
assert audit['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' and sha(raw(audit_path))=='74dff3d3134d490e73db6bf5ed24ab9a7c8e4724f81c867a4906fd2431ca3800'
assets=load(N/'assets_observation_v1.json');assert assets['parent_exit']=='0' and assets['parent_completion']['checkpoint_sha256']==audit['checkpoint']['sha256']
q=load(N/'training_entry_request_candidate_v1.json');base=load(D/'training_entry_request_v1.json')
ep=I/'bcsp_training_entry_foldD_16384_v8.py';cp=I/'bcsp_training_contract_foldD_16384_v6.py'
oldcp=D/'implementation_v1/bcsp_training_contract_foldD_8192_v5.py';oldentry=D/'implementation_v1/bcsp_training_entry_foldD_8192_v7.py'
assert cp.read_text()==oldcp.read_text().replace("require(q['fold'] == 'D' and q['n_input'] == 8192, 'Fold D 8k arm only')","require(q['fold'] == 'D' and q['n_input'] == 16384, 'Fold D 16k arm only')")
assert ep.read_text()==oldentry.read_text().replace(oldcp.name,cp.name).replace(sha(raw(oldcp)),sha(raw(cp)))
pair=load(N/'paired315_data_verification_v1.json');assert pair['train_cases']==315 and pair['all_targets_byte_identical'] and pair['all8192_inputs_are_16384_prefixes']
p3=dump('local_P3_v1.json',dict(status='PASS_FOLD_D16_FULL_AUTHORIZE_AND_MINIMAL_INTERFACE',date_Asia_Shanghai='2026-10-26',CPU_contracts=results,
 controller_metadata_predicates=dict(positive=4,negative=3),only_contract_change='Dedicated D8192 toD16384 arm gate and error text',only_entry_change='Sibling module filename/SHA',
 same_model_runtime_order_target_backend_numeric_resources=True,server_writes=0,CUDA_calls=0,
 files=[bind(p) for p in [ep,cp,I/'test_full_authorize_v1.py',I/'cpu_process_capture_v1.json',I/'cpu_stdout_v1.log',I/'cpu_stderr_v1.log',I/'cpu_contract_v1/results_v1.json',N/'candidate_static_review_v1.json',N/'paired315_data_verification_v1.json']],
 CPU_fixture_inventory=[dict(file=str(p.relative_to(N)),bytes=p.stat().st_size,sha256=sha(raw(p))) for p in sorted((I/'cpu_contract_v1').rglob('*')) if p.is_file()],
 limitation='CPUcontracts and prior C16 success do not certify completion of this D16 attempt;retain existing resource ceilings and stop policy'))
qp=N/'training_entry_request_v1.json'
with qp.open('xb') as f:f.write(raw(N/'training_entry_request_candidate_v1.json'))
CODE=q['implementation']['entry']['path'].rsplit('/',1)[0];DATA=q['data_root'];CONTROL=q['launch_attempt'].rsplit('/',1)[0];OUT=q['output']
items=[]
for r in pair['case_rows']:items.append(dict(archive_member=r['point_path'],target=DATA+'/'+r['point_path'],bytes=r['bytes'],sha256=r['sha256'],local_file=str((B/'real_data_qc_v1'/r['point_path']).absolute())))
qual=N/'qualified_data_qc_foldD_16384_v1.json'
for p,target in [(ep,q['implementation']['entry']['path']),(cp,q['implementation']['contract']['path']),(qual,q['QC']['qualified_receipt']['path'])]:
 items.append(dict(archive_member='code/'+p.name,target=target,bytes=len(raw(p)),sha256=sha(raw(p)),local_file=str(p.absolute())))
assert len(items)==318
mapping=dump('installation_mapping_v1.json',dict(schema='bcsp-foldD-16384-minimal-installation-v1',status='PREPARED_NOT_DEPLOYED',expected_identity=q['identity'],project=q['identity']['project'],code_root=CODE,data_root=DATA,
 directories=[DATA,DATA+'/points'],files=items,reused_static=q['static_config'],reused_order=q['order_plan'],reused_runtime=q['implementation']['runtime'],
 rules=['Recheck identity,archive hash,all318 targets absent and safe parents before writing','Exclusive no-follow creation;two listed data directories only;no overwrites','Verify318 installed hashes,315 allowlisted payloads and reused exact FoldDorder before single launch','Failure stops;no retry/resume/batch/backend changes or automatic cleanup']))
archive=N/'bcsp_foldD_16384_seed0_inputs_and_entry_v1.tar.gz'
with archive.open('xb') as out:
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  for r in items:
   data=raw(r['local_file']);assert len(data)==r['bytes'] and sha(data)==r['sha256']
   ti=tarfile.TarInfo(r['archive_member']);ti.size=len(data);ti.mode=0o644;ti.mtime=0
   tf.addfile(ti,io.BytesIO(data))
with (N/(archive.name+'.sha256')).open('x') as f:f.write(sha(raw(archive))+'  '+archive.name+'\n')
with (N/'bcsp_foldD_16384_seed0_inputs_and_entry_v1.contents.sha256').open('x') as f:
 for r in items:f.write(r['sha256']+'  '+r['archive_member']+'\n')
s=load(D/'training_execution_request_v1.json');old_control=base['launch_attempt'].rsplit('/',1)[0];old_out=base['output']
def rewrite(v):
 if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
 if isinstance(v,list):return [rewrite(x) for x in v]
 if isinstance(v,str):return v.replace(old_control,CONTROL).replace(old_out,OUT).replace('bcsp_geov1_b0_foldd_in8192_seed0_train_v1','bcsp_geov1_b0_foldd_in16384_seed0_train_v1')
 return v
s=rewrite(s);s['run_id']=q['run_id'];s['request_version']=1;s['actual_training_attempt_index']=1
s['request_kind']='Final planned matrix arm Fold D16k-input/8k-target;one scratch run after exclusive318-file install;no new sampling/model/backend/order'
s['entry_request']=bind(qp,CONTROL+'/training_execution_request_v1.json')
s['parent_evidence']=dict(resources=bind(N/'resources_observation_v1.json'),reused_assets=bind(N/'assets_observation_v1.json'),fresh_paths=bind(N/'freshness_observation_v1.json'),paired_D_data=bind(N/'paired315_data_verification_v1.json'),implementation_P3=bind(p3),FoldD8_freeze=bind(audit_path))
s['paired_8k_parent']=dict(run_id=base['run_id'],freeze_audit=bind(audit_path),checkpoint_SHA256=audit['checkpoint']['sha256'],checkpoint_used_for_initialization=False,
 expected_same_initialization=assets['parent_initialization'],post_training_requirement='Compare initial parameters,persistent state,seed,order,actual3900 batches and exposures toD8 before interpreting pair')
s['scientific_contract']['input_points']=16384;s['scientific_contract']['qualified_QC']=q['QC']['qualified_receipt']
s['scientific_contract']['real_payload_scope']='Only315 exact Fold D train16k NPZ;targets byte-identical toD8,8k partials exact prefixes;no FoldDdevelopment or confirmation payloads'
res=load(N/'resources_observation_v1.json')
s['resource_snapshot_evidence']=dict(UTC=res['UTC'],GPU_memory_used_MiB=1,compute_processes=0,disk_free_bytes=res['disk']['free'],not_persistent_admission=True,recheck_before_launch=True)
s['future_materialization_contract']['authorization_schema']['request_sha256']=sha(raw(qp));s['future_materialization_contract']['runtime_schema']['request_sha256']=sha(raw(qp))
argv=s['future_materialization_contract']['external_training_argv'];argv[8]=q['implementation']['entry']['path'];argv[argv.index('--request-sha256')+1]=sha(raw(qp))
s['prelaunch_guards'][1]='Verify318-file data/QC/module installation plus existing frozen model/provider/static/runtime and exact shared FoldDorder;no inventory expansion or downloads'
s['local_serialization']['controller_template']=bind(N/'controller_template_foldD_16384_v1.py')
s['local_serialization']['future_rendering_contract'][0]='Only after a new fullSHA grant and verified318-file installation,load exact raw finalscope,strict D16entry request and current-device risk record;validate every bound hash before rendering.'
s['previous_attempt']=dict(status='FIRST_ATTEMPT_FOR_FOLD_D_16384',earlier_grants_reusable=False,new_attempt_is_scratch=True)
s['known_failure_and_diagnostic_scope']=dict(dedicated_FoldD16384_gate=True,same_FoldD_order_pin=True,actual_authorize_CPU_tests_passed=15,all_resource_thresholds_unchanged=True,PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',no_new_GPU_preflight=True)
s['minimal_deployment']=dict(status='PREPARED_NOT_DEPLOYED',installation_mapping=bind(mapping),archive=bind(archive),future_upload_path='/home/jovyan/'+archive.name,
 full_scope_execution_authorization_covers='After manual upload,exclusive318-file installation and readback hashes;reverify reused exact FoldDorder;one fresh D16 tmux training attempt',failure_stops_before_training=True,installed_verification_required_before_controller=True)
s['FoldD_design'].pop('paired_16k_training_not_authorized',None)
s['FoldD_design']['paired_16k_status']='THIS_REQUEST_PENDING_SEPARATE_EXPLICIT_EXECUTION_AUTHORIZATION'
s['current_task_boundary']=dict(server_operations='One readonly D8formal freeze audit plus three bounded preparation queries;no writes orGPUcompute',server_writes=0,CUDA_calls=0,
 local_files='D16paired proof,two dedicated modules,15 actual authorize CPUcontracts,P3,transport andpending requests',production_authorization_created=False,runtime_config_created=False,launcher_created=False,training_started=False)
s['next']='Upload exact318-file archive;separately authorize this fullSHA for frozen installation and one D16 run. No automatic BNCal,evaluation,additional seeds or followup runs.'
op=dump('training_execution_request_v1.json',s)
assert {k for k in q if q[k]!=base[k]}=={'run_id','n_input','QC','data_root','implementation','output','launch_attempt'}
assert q['order_plan']==base['order_plan'] and q['static_config']==base['static_config'] and q['fold']==base['fold']=='D'
assert s['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and s['execution_authorized'] is False
with (N/'training_execution_request_v1.json.sha256').open('x') as f:f.write(sha(raw(op))+'  '+op.name+'\n')
print(json.dumps(dict(status='PREPARED_AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(op),archive=bind(archive),files=318,CPU_authorize_contracts_passed=15,server_writes=0,training_started=False)))
