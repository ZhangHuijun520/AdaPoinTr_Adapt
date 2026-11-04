"""Freeze local two-file hotfix and fresh pending request; no remote action."""
from pathlib import Path
import copy,hashlib,io,json,tarfile
N=Path(__file__).resolve().parent;OLD=N.parent;B=OLD.parent
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
def raw(p):return Path(p).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def bind(p,server=None):
 p=Path(p).absolute();v=dict(path=str(p),bytes=len(raw(p)),sha256=sha(raw(p)))
 if server:v['future_server_path']=server
 return v
def remote(p,target):return dict(path=target,bytes=len(raw(p)),sha256=sha(raw(p)))
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p

results=load(N/'cpu_contract_v1/results_v1.json');assert results['status']=='PASS_14_FULL_AUTHORIZE_CPU_CONTRACTS'
assert sha(raw(P/'bcsp_training_contract_01dt08_v3.py'))=='08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499'
assert sha(raw(P/'bcsp_training_entry_research_v5.py'))=='a01a9c3c3e2dbe582db4f2a196771ae2cd755aab20f20f1c9dd34f3f9ce37dce'
old_scope=load(OLD/'training_execution_request_v1.json')
assert sha(raw(OLD/'training_execution_request_v1.json'))=='ebb8d4051cc405939930a41fc292d55a81fe6cf5dc786c77a62b5a6317c46a4a'
installed=load(OLD/'authorized_execution_v2/install_server_events_v1.json')
assert any(r.get('status')=='DATA316_INSTALLATION_HASH_PASS' and r['installed_files']==316 for r in installed)
ep=N/'bcsp_training_entry_foldC_16384_v6.py';cp=N/'bcsp_training_contract_foldC_16384_v4.py'
p3=dump('local_P3_v2.json',dict(status='PASS_DEDICATED_16K_AUTHORIZE_HOTFIX',date_Asia_Shanghai='2026-10-26',
 actual_authorize_function_tested=True,entry_bootstrap_exercised=True,metadata_functions_not_mocked=True,CPU_contracts=results,
 contract_change='Only q.fold==C and q.n_input==16384 gate plus error text;old8k contract untouched',entry_change='Sibling contract filename and exact SHA only',
 model_runtime_data_order_numeric_resources_unchanged=True,server_operations=0,CUDA_calls=0,
 files=[bind(x) for x in [ep,cp,N/'test_full_authorize_v1.py',N/'static_review_v1.json',N/'cpu_process_capture_v1.json',N/'cpu_stdout_v1.log',N/'cpu_stderr_v1.log',N/'cpu_contract_v1/results_v1.json']],
 CPU_fixture_inventory=[dict(file=str(p.relative_to(N)),bytes=p.stat().st_size,sha256=sha(raw(p))) for p in sorted((N/'cpu_contract_v1').rglob('*')) if p.is_file()],
 limitations=['CPUauthorization success is not CUDA completion or16k full training memory guarantee','Fresh production targets/resources must be checked at execution;no server operation this turn']))
q=load(OLD/'training_entry_request_v1.json');oldq=copy.deepcopy(q)
CODE=q['implementation']['entry']['path'].rsplit('/',1)[0]
CONTROL=CODE+'/control_train_foldC_16384_v2'
OUT=q['output'].replace('_train_v1','_train_v2')
q['run_id']=q['run_id'].replace('_train_v1','_train_v2');q['output']=OUT;q['launch_attempt']=CONTROL+'/launch_attempt_v1.json'
q['implementation']['entry']=remote(ep,CODE+'/'+ep.name);q['implementation']['contract']=remote(cp,CODE+'/'+cp.name)
qp=dump('training_entry_request_v2.json',q)
files=[dict(archive_member=p.name,target=CODE+'/'+p.name,bytes=len(raw(p)),sha256=sha(raw(p)),local_file=str(p)) for p in [ep,cp]]
mapping=dump('two_file_installation_mapping_v2.json',dict(schema='bcsp-foldC-16384-authorization-hotfix-installation-v2',status='PREPARED_NOT_DEPLOYED',expected_identity=q['identity'],
 files=files,new_directories=[],code_root=CODE,reuse_installed_data=True,data_root=q['data_root'],
 reused_data_installation=bind(OLD/'authorized_execution_v2/install_server_events_v1.json'),reused315_data_mapping=bind(OLD/'minimal_installation_mapping_v1.json'),qualified_QC=q['QC']['qualified_receipt'],
 rules=['Recheck identity,upload hash,two exact targets absent and safe existing parent','Exclusive no-follow creation;no overwrite;read back both hashes','Do not reinstall315 point files orQC;reverify existing315 payload/QC hashes before launch','Old control/output/request remain consumed and unchanged','Any execution failure stops;no automatic retry/resume/backend or batch changes']))
archive=N/'bcsp_foldC_16384_authorize_hotfix_v2.tar.gz'
with archive.open('xb') as out:
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  for p in [ep,cp]:
   ti=tarfile.TarInfo(p.name);ti.size=len(raw(p));ti.mode=0o644;ti.mtime=0
   tf.addfile(ti,io.BytesIO(raw(p)))
with (N/(archive.name+'.sha256')).open('x') as f:f.write(sha(raw(archive))+'  '+archive.name+'\n')
with (N/'bcsp_foldC_16384_authorize_hotfix_v2.contents.sha256').open('x') as f:
 for p in [ep,cp]:f.write(sha(raw(p))+'  '+p.name+'\n')
old_control=oldq['launch_attempt'].rsplit('/',1)[0];old_out=oldq['output']
def rewrite(x):
 if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
 if isinstance(x,list):return [rewrite(v) for v in x]
 if isinstance(x,str):return x.replace(old_control,CONTROL).replace(old_out,OUT).replace('bcsp_geov1_b0_foldc_in16384_seed0_train_v1','bcsp_geov1_b0_foldc_in16384_seed0_train_v2')
 return x
s=rewrite(old_scope);s['run_id']=q['run_id'];s['request_version']=2;s['actual_training_attempt_index']=2
s['request_kind']='One new scratch16k attempt after dedicated authorize gate fix;two code files installed exclusively;reuse all316 installed data/QC files'
s['entry_request']=bind(qp,CONTROL+'/training_execution_request_v1.json')
s['parent_evidence'].update(authorize_hotfix_P3=bind(p3),full_authorize_CPU_results=bind(N/'cpu_contract_v1/results_v1.json'),failed_attempt=bind(OLD/'execution_failure_receipt_v1.json'),data_installation=bind(OLD/'authorized_execution_v2/install_server_events_v1.json'))
s['future_materialization_contract']['authorization_schema']['request_sha256']=sha(raw(qp));s['future_materialization_contract']['runtime_schema']['request_sha256']=sha(raw(qp))
argv=s['future_materialization_contract']['external_training_argv'];argv[8]=q['implementation']['entry']['path'];argv[argv.index('--request-sha256')+1]=sha(raw(qp))
s['prelaunch_guards'][1]='Verify the two new module hashes and existing315 data/QC/static/order/model/provider bindings;no data reinstall or broad inventory'
s['resource_snapshot_evidence']['not_refreshed_this_turn']=True
s['previous_attempt']=dict(status='FAILED_BEFORE_MODEL_IMPORT_CONSUMED_DO_NOT_REUSE',run_id=oldq['run_id'],execution_scope_sha256='ebb8d4051cc405939930a41fc292d55a81fe6cf5dc786c77a62b5a6317c46a4a',
 failure_receipt=bind(OLD/'execution_failure_receipt_v1.json'),exit_code=1,committed_updates=0,forward_calls=0,reason='Previous contract restricted n_input to8192',old_control=old_control,old_output=old_out,new_attempt_is_scratch=True)
s['known_failure_and_diagnostic_scope']=dict(dedicated_16k_authorize_gate_fixed=True,actual_authorize_path_CPU_tests_passed=14,old_8k_path_unchanged=True,
 production_changes='One arm gate and sibling module binding only',PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',all_resource_thresholds_unchanged=True,full16k_training_fit_not_guaranteed=True)
s['minimal_deployment']=dict(status='PREPARED_NOT_DEPLOYED',installation_mapping=bind(mapping),archive=bind(archive),future_upload_path='/home/jovyan/'+archive.name,
 full_scope_execution_authorization_covers='After manual upload,exclusive installation/readback of only two new modules;reverify existing315 training payloads andQC;one fresh16k tmux training attempt',
 reuse_installed_data=True,reinstall_data=False,failure_stops_before_training=True,installed_verification_required_before_controller=True)
s['current_task_boundary']=dict(server_operations=0,local_changes='Two dedicated modules;14 actual authorize CPUcontracts;localP3;two-file transport;newpending request',
 runtime_config_created=False,launcher_created=False,training_execution_authorization_created=False,artificial_CPU_authorization_fixture_files=True,training_steps=0)
s['next']='Upload two-module archive;separately authorize this new fullSHA for exclusive deployment and one new training attempt. Old request is consumed. No data reupload or reinstall.'
op=dump('training_execution_request_v2.json',s)
assert {k for k in q if q[k]!=oldq[k]}=={'run_id','implementation','output','launch_attempt'}
assert {k for k in q['implementation'] if q['implementation'][k]!=oldq['implementation'][k]}=={'entry','contract'}
for key in ['static_config','order_plan','QC','data_root','identity','n_input']:assert q[key]==oldq[key]
assert s['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and s['execution_authorized'] is False
with (N/'training_execution_request_v2.json.sha256').open('x') as f:f.write(sha(raw(op))+'  '+op.name+'\n')
print(json.dumps(dict(status='FROZEN_AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(op),archive=bind(archive),data_reupload=False,server_operations=0)))
