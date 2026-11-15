"""Local P3 and new consumed-predecessor-safe request; no server access or real SMI."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_D_implementation_20261115_v1';O=B/'selector_diagnostic_hotfix_v2'
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
ctx=read(O/'implementation_context_v2.json');q=copy.deepcopy(ctx['candidate']);mirror={k:Path(v) for k,v in ctx['mirror'].items()};old=ctx['parent_consumed_request']
entry=O/'bcsp_scq_rf_Static_D_training_entry_v2.py';test=O/'test_Static_D_selector_diagnostic_cpu_v3.py';cp=O/'cpu_selector_diagnostic_batch_v3';cpu=read(cp/'result_v1.json');static=read(O/'static_review_v2.json')
assert cpu['status']=='RF_STATIC_D_SELECTOR_DIAGNOSTIC_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==71
assert cpu['entry']==rec(entry)==static['entry'] and cpu['test']==rec(test) and cpu['bridge']['sha256']==q['implementation']['bridge']['sha256']
assert not (cp/'failure_v1.json').exists() and (cp/'policy_stderr.bin').stat().st_size==0 and all(read(cp/'policy_stdout.bin').values())
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['checkpoint_loads']==cpu['real_payload_arrays_read']==0
first=O/'test_Static_D_selector_diagnostic_cpu_v2.py';t0=first.read_text(encoding='utf-8');t1=test.read_text(encoding='utf-8')
assert t1.replace('cpu_selector_diagnostic_batch_v3','cpu_selector_diagnostic_batch_v2').replace('Popen=FakeProcess,PIPE=subprocess.PIPE,TimeoutExpired=','Popen=FakeProcess,TimeoutExpired=')==t0
fixture_failure=O/'cpu_selector_diagnostic_batch_v2/failure_v1.json';assert read(fixture_failure)['status']=='FAILED_STOP_NO_RETRY'
emit(O/'fixture_correction_review_v3.json',dict(status='TEST_FIXTURE_PIPE_ONLY_STATIC_PASS',old_test=rec(first),new_test=rec(test),failed_batch_preserved=rec(fixture_failure),production_entry_unchanged=rec(entry),change='Add PIPE=subprocess.PIPE to fake subprocess namespace; full new output directory; no production/threshold changes'))
audit=B/'failed_startup_SMI_review_v1/freeze_verification_v1.json';a=read(audit);assert a['status']=='FORMAL_STATIC_D_FAILED_STARTUP_FREEZE_AUDIT_PASS' and a['count']==14 and all(a['checks'].values()) and a['committed_updates']==0
for key in old:
 if key not in ('implementation','environment','run_id','output','launch_attempt','launch_contract','status'):assert q[key]==old[key]
for key,r in old['implementation'].items():
 if key!='entry':assert q['implementation'][key]==r
assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'] and old['environment']['CUDA_VISIBLE_DEVICES']==q['historical_identity']['gpu_uuid']
assert all(q['environment'][k]==v for k,v in old['environment'].items() if k!='CUDA_VISIBLE_DEVICES')
of={n.name:ast.dump(n,include_attributes=False) for n in ast.parse((B/'bcsp_scq_rf_Static_D_training_entry_v1.py').read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
nf={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(entry.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','validate_continuation','scq_geometry','dispatch_training','make_budget','startup_read_records']
assert all(of[k]==nf[k] for k in unchanged) and static['source_read_roots_unchanged']
for mode in ['nonzero','success','timeout']:
 p=cp/'ARTIFICIAL_FIXTURES'/('startup_query_'+mode)/'startup_monitor_failure.json'
 if mode=='success':assert not p.exists()
 else:
  d=read(p)['details'];assert d['command'][1]=='--id='+q['identity']['gpu_uuid'] and d['timeout_seconds']==10 and d['query_attempts']==1 and d['returncode']==(9 if mode=='nonzero' else -9)
p3=dict(status='RF_STATIC_D_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'],native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=71,CPU=rec(cp/'result_v1.json'),test=rec(test),static=rec(O/'static_review_v2.json'),fixture_correction=rec(O/'fixture_correction_review_v3.json'),prior_failure_freeze=rec(audit),unchanged_parent_functions=unchanged,
 checks=dict(all71_CPU_checks_pass=True,current_selector_matches_identity_and_launcher_and_real_helper_argv=True,only_selector_environment_delta=True,numerical_environment_preserved=True,bounded_failure_details_stdout_stderr_returncode_persisted=True,nonzero_success_timeout_fake_cases=True,SMI_10second_budget_and2second_reap_unchanged=True,no_query_retry_added=True,model_loss_runtime_data_order3900_resources_unchanged=True,accepted_cross_device_limits_preserved=True,complete_source_read_chain_and_traceback=True),
 limitations=cpu['limitations']+['The first new batch failed because its fake subprocess lacked PIPE; failure retained and only fixture corrected in a fresh version.','SMI helper tested with fake child only; no actual server/GPU/nvidia-smi invoked.','Current native CUDA remains untested in this CPU batch. D comparison remains device-confounded.'],server_operations=0,training=False,CUDA=False)
emit(O/'training_entry_P3_v2.json',p3)
T=O/'pending_transport_v2';T.mkdir();P=T/'payload';P.mkdir()
for p in [entry,test,O/'training_entry_P3_v2.json',O/'static_review_v2.json',O/'fixture_correction_review_v3.json']:shutil.copyfile(p,P/p.name)
shutil.copyfile(cp/'result_v1.json',P/'training_CPU_result_v3.json');shutil.copyfile(audit,P/'Static_D_v1_failed_freeze_v1.json')
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False;q['P3']=rec(P/'training_entry_P3_v2.json',C+'/training_entry_P3_v2.json');q['CPU_evidence']=rec(P/'training_CPU_result_v3.json',C+'/training_CPU_result_v3.json')
q['supersedes']=dict(request_sha256='b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6',status='CONSUMED_FAILED_BEFORE_MODEL_ZERO_UPDATES_NO_REUSE',failure_freeze=rec(P/'Static_D_v1_failed_freeze_v1.json',C+'/Static_D_v1_failed_freeze_v1.json'))
q['limited_fix']='Exact accepted current GPU selector only; numerical env unchanged; bounded startup MonitorQueryFailure details persisted; one query, no retry or threshold changes.'
q['activation_prerequisites'][2]='Verify archive+3 sidecars; all8 new targets/control/output absent; no overwrite. Reverify all reused v1 migration/readiness/frozen-reference files and accepted current identity plus D315 payload hashes.'
bindings={r['path']:r for r in q['reused_readonly_bindings']}
for r in [q['accepted_device_migration'],q['readiness'],*[v for k,v in q['paired_baseline'].items()],*[v for k,v in q['paired_requery'].items()],*q['continuation_evidence'].values()]:
 if r['path'] in bindings:assert bindings[r['path']]==r
 else:bindings[r['path']]=r
q['reused_readonly_bindings']=list(bindings.values())
request=P/'SCQ_RF_Static_D_training_execution_request_v2.json';emit(request,q);qh=rec(request)['sha256']
mirror[q['P3']['path']]=P/'training_entry_P3_v2.json';mirror[q['CPU_evidence']['path']]=P/'training_CPU_result_v3.json';mirror[q['launch_contract']['request_path']]=request
spec=importlib.util.spec_from_file_location('Static_D_v2_final_metadata_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
x=e.exact;e.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
sm=e.source_module
def mod(name,r):
 m=sm(name,r)
 if name=='bcsp_training_contract_v1':
  ex=m.exact;m.exact=lambda r:ex(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else ex(r)
 return m
e.source_module=mod
auth=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='MEMORY_ONLY_FINAL_CONTRACT_NOT_EXECUTION_AUTHORIZATION');runtime=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
bd=e.bound;e.bound=lambda r:auth if r['path']=='MEMORY_AUTH' else runtime if r['path']=='MEMORY_RUNTIME' else bd(r)
sys.modules.pop('bcsp_training_contract_v1',None)
v=e.authorize(rec(request,q['launch_contract']['request_path']),dict(path='MEMORY_AUTH',bytes=0,sha256='a'*64),dict(path='MEMORY_RUNTIME',bytes=0,sha256='b'*64))
assert len(v[3])==315 and v[-1]==ctx['expected_common'] and v[2].canonical_sha(v[5])=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
launcher=e.render_launcher(q,qh,'a'*64,'b'*64)
assert 'export CUDA_VISIBLE_DEVICES='+q['identity']['gpu_uuid'] in launcher and q['historical_identity']['gpu_uuid'] not in launcher and launcher.index('mkdir -p')<launcher.index(' >') and max(len(l.encode()) for l in launcher.splitlines())<=2048
assert q['run_id']!=old['run_id'] and q['output']!=old['output'] and q['launch_attempt']!=old['launch_attempt']
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=C,files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'])
assert len(mapping['files'])==8;emit(T/'installation_mapping_v2.json',mapping)
arc=T/'bcsp_scq_rf_Static_D_selector_diag_pending_20261115_v2.tar.gz'
with arc.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  t.add(T/'installation_mapping_v2.json',arcname='installation_mapping_v2.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as t:
 members=t.getmembers();assert len(members)==9 and all(m.isfile() for m in members);listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
 with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'final_authorize_review_v2.json',dict(status='STATIC_D_V2_FINAL_AUTHORIZE_LAUNCHER_PASS',request=rec(request),CPU_checks=71,selector=q['environment']['CUDA_VISIBLE_DEVICES'],current_identity=q['identity'],prior_request_consumed=True,controls_materialized=False,server_operations=0))
emit(O/'final_local_mirror_v2.json',{k:str(v.resolve()) for k,v in mirror.items()})
emit(O/'delivery_v2.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),mapping=rec(T/'installation_mapping_v2.json'),P3=rec(O/'training_entry_P3_v2.json'),CPU_checks=71,install_files=8,archive_members=9,controls_materialized=False,server_operations=0,training=False,CUDA=False,cross_device_D_comparison=True))
print(json.dumps(dict(status='STATIC_D_SELECTOR_DIAGNOSTIC_P3_PASS_V2_REQUEST_PENDING',CPU_checks=71,request_sha256=qh,archive=rec(arc))))
