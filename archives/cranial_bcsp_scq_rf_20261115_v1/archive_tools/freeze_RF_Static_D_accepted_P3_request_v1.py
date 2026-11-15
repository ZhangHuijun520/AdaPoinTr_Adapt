"""Local Static_D P3 + pending request; accepted migration is not execution permission."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_Static_D_implementation_20261115_v1'
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
ctx=read(O/'implementation_context_v1.json');q=copy.deepcopy(ctx['candidate']);mirror={k:Path(v) for k,v in ctx['mirror'].items()}
entry=O/'bcsp_scq_rf_Static_D_training_entry_v1.py';bridge=mirror[q['implementation']['bridge']['path']];test=O/'test_RF_Static_D_entry_cpu_v1.py';cp=O/'cpu_static_D_entry_batch_v1';cpu=read(cp/'result_v1.json');static=read(O/'static_review_v1.json')
assert cpu['status']=='RF_STATIC_D_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==62
assert cpu['entry']==rec(entry)==static['entry'] and cpu['bridge']==rec(bridge) and cpu['test']==rec(test)
assert not (cp/'failure_v1.json').exists() and (cp/'policy_stderr.bin').stat().st_size==0
policy=read(cp/'policy_stdout.bin');assert all(policy.values()) and policy['all17_source_traceback_lines'] and policy['complete_source_load_order'] and policy['original_exception_preserved']
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['checkpoint_loads']==cpu['real_payload_arrays_read']==0
for r in [*q['implementation'].values(),q['initialization'],q['rf_initialization'],q['accepted_device_migration'],q['readiness']]:
 p=mirror[r['path']];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes']
migration=read(mirror[q['accepted_device_migration']['path']]);assert migration['historical_identity']==q['historical_identity'] and migration['current_identity']==q['identity'] and migration['execution_authorized'] is False
assert sorted(k for k in q['identity'] if q['identity'][k]!=q['historical_identity'][k])==migration['allowed_changed_fields']==['driver_version','gpu_uuid','hostname']
assert q['comparison_qualification']==migration['interpretation'] and not migration['interpretation']['strict_same_device_D_pair']
assert q['identity']['hostname']=='shu-common-25721452-notebook-qx2k0r-0' and q['identity']['gpu_uuid']=='GPU-383d118a-368c-94e3-166a-cad3efab8fd7' and q['identity']['driver_version']=='570.190'
old=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1/bcsp_scq_rf_Requery_D_training_entry_v1.py'
of={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(old.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)};nf={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(entry.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','startup_read_records']
assert all(of[k]==nf[k] for k in unchanged) and static['source_read_roots_unchanged']
assert read(mirror[q['paired_baseline']['audit']['path']])['check_count']==30
ra=read(mirror[q['paired_requery']['audit']['path']]);ri=read(mirror[q['paired_requery']['initialization']['path']])
assert ra['status']=='FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' and ra['check_count']==43 and all(ra['checks'].values()) and ra['identity']==q['historical_identity']
assert q['expected_model_initialization']=={k:ri[k] for k in ['parameter_sha256','persistent_state_sha256','seed']} and ri['order_sha256']=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
native=read(mirror[q['admission']['construction']['path']]);assert native['models'][1]['phase']=='Static_eval1' and native['models'][1]['parameters']==40827847
p3=dict(status='RF_STATIC_D_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=rec(bridge)['sha256'],native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=62,CPU=rec(cp/'result_v1.json'),test=rec(test),static=rec(O/'static_review_v1.json'),policy_stdout=rec(cp/'policy_stdout.bin'),accepted_migration=q['accepted_device_migration'],comparison_qualification=q['comparison_qualification'],historical_identity=q['historical_identity'],current_frozen_identity=q['identity'],unchanged_parent_functions=unchanged,
 checks=dict(all62_CPU_pass=True,exact_accepted_old_new_identities=True,arbitrary_hardware_or_software_identity_drift_rejected=True,historical_identity_not_rewritten=True,false_strict_pair_claim_rejected=True,Static_N0_reuse_and_Q1_geometry=True,full_RF_forward_loss_backward_artificial=True,source_bridge_runtime_and_formula_unchanged=True,source_init_read_policy_and_traceback=True,SCQ_RF_parameter_groups_unchanged=True,D_order3900_and_frozen_references=True,training_resources_thresholds_unchanged=True),
 limitations=cpu['limitations']+['Historical GPU admission is implementation evidence only; actual CUDA on current GPU/driver has NOT been tested in this batch.','D Static/Requery comparison is explicitly confounded by device and driver. No unconditional mechanism attribution.','Current software/provider hashes, real315 payload hashes and resources still need fresh checks before separately authorized execution.','No matching retraining, retry/resume or protocol tuning authorized.'],server_operations=0,training=False,CUDA=False)
emit(O/'training_entry_P3_v1.json',p3)
T=O/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
for p in [entry,test,O/'static_review_v1.json',O/'training_entry_P3_v1.json',O/'Static_D_accepted_device_migration_v1.json',O/'Static_D_current_identity_readiness_v1.json']:shutil.copyfile(p,P/p.name)
shutil.copyfile(cp/'result_v1.json',P/'training_CPU_result_v1.json')
for key,name in [('paired_baseline','Sref_D_formal_freeze_v1.json'),('paired_requery','Requery_D_formal_freeze_v1.json')]:
 p=P/name;shutil.copyfile(mirror[q[key]['audit']['path']],p);q[key]['audit']=rec(p,C+'/'+name);mirror[C+'/'+name]=p
for name,r in list(q['continuation_evidence'].items()):
 p=P/(name+'_formal_freeze_v1.json');shutil.copyfile(mirror[r['path']],p);q['continuation_evidence'][name]=rec(p,C+'/'+p.name);mirror[C+'/'+p.name]=p
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False;q['P3']=rec(P/'training_entry_P3_v1.json',C+'/training_entry_P3_v1.json');q['CPU_evidence']=rec(P/'training_CPU_result_v1.json',C+'/training_CPU_result_v1.json')
q['activation_prerequisites'][2]='Verify archive+3 sidecars; all13 new targets/control/output absent; no overwrite. Exact accepted current device/driver and unchanged software/provider/source/init plus315 D payload hashes required.'
q['activation_prerequisites'][1]='Fresh exact accepted qx2k0r GPU-383d118a driver570.190 and pinned interpreter/software/provider; never auto-rebind. Historical devices remain provenance only.'
q['training_reference']='Final frozen run Static_D: scratch seed0, no checkpoint warmstart, same D315/order3900/loss/optimizer/resources. User accepted exact device migration; D comparison is device-confounded supplementary evidence, C pair remains same-device evidence. No automatic matching retrain.'
bindings={r['path']:r for r in q['reused_readonly_bindings']}
for r in [*[v for k,v in q['implementation'].items() if k!='entry'],q['initialization'],q['rf_initialization'],q['pair_contract'],q['order_plan'],q['QC']['qualified_receipt'],q['QC']['verification'],*q['QC']['manifests'].values(),q['QC']['fold_binding'],*[v for k,v in q['paired_baseline'].items() if k!='audit'],*[v for k,v in q['paired_requery'].items() if k!='audit']]:
 if r['path'] in bindings:assert bindings[r['path']]==r
 else:bindings[r['path']]=r
q['reused_readonly_bindings']=list(bindings.values())
request=P/'SCQ_RF_Static_D_training_execution_request_v1.json';emit(request,q);qh=rec(request)['sha256']
for r,p in [(q['P3'],P/'training_entry_P3_v1.json'),(q['CPU_evidence'],P/'training_CPU_result_v1.json')]:mirror[r['path']]=p
mirror[q['launch_contract']['request_path']]=request
spec=importlib.util.spec_from_file_location('Static_D_final_metadata_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
x=e.exact;e.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
sm=e.source_module
def mod(name,r):
 m=sm(name,r)
 if name=='bcsp_training_contract_v1':
  ex=m.exact;m.exact=lambda r:ex(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else ex(r)
 return m
e.source_module=mod
a=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='MEMORY_ONLY_FINAL_REVIEW_NOT_USER_EXECUTION_AUTHORIZATION');rt=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
bd=e.bound;e.bound=lambda r:a if r['path']=='MEMORY_AUTH' else rt if r['path']=='MEMORY_RUNTIME' else bd(r)
sys.modules.pop('bcsp_training_contract_v1',None)
v=e.authorize(rec(request,q['launch_contract']['request_path']),dict(path='MEMORY_AUTH',bytes=0,sha256='a'*64),dict(path='MEMORY_RUNTIME',bytes=0,sha256='b'*64))
assert len(v[3])==315 and v[-1]==ctx['expected_common'] and v[2].canonical_sha(v[5])=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
assert v[-2]['native_validation_scope']=='HISTORICAL_IMPLEMENTATION_ONLY'
launcher=e.render_launcher(q,qh,'a'*64,'b'*64);assert launcher.index('mkdir -p')<launcher.index(' >') and max(len(l.encode()) for l in launcher.splitlines())<=2048
parent=ctx['parent_Requery_D_request']
for key in ['science','resources','initialization','QC','order_plan','static_config','admission','dependencies','environment','pair_contract','data_root','model_root','preflight_scope','rf_initialization']:assert q[key]==parent[key]
assert q['historical_identity']==parent['identity'] and q['identity']==migration['current_identity']
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=C,files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'])
assert len(mapping['files'])==13;emit(T/'installation_mapping_v1.json',mapping)
arc=T/'bcsp_scq_rf_Static_D_pending_20261115_v1.tar.gz'
with arc.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as t:
 members=t.getmembers();assert len(members)==14 and all(m.isfile() for m in members)
 listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
 with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'final_authorize_review_v1.json',dict(status='STATIC_D_ACCEPTED_DEVICE_MIGRATION_FINAL_CONTRACT_PASS',request=rec(request),CPU_checks=62,D_order_canonical=v[2].canonical_sha(v[5]),current_identity=q['identity'],historical_identity=q['historical_identity'],comparison_qualification=q['comparison_qualification'],controls_materialized=False,server_operations=0))
emit(O/'final_local_mirror_v1.json',{k:str(v.resolve()) for k,v in mirror.items()})
emit(O/'delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),mapping=rec(T/'installation_mapping_v1.json'),P3=rec(O/'training_entry_P3_v1.json'),CPU_checks=62,install_files=13,archive_members=14,controls_materialized=False,server_operations=0,training=False,CUDA=False,cross_device_D_comparison=True))
print(json.dumps(dict(status='STATIC_D_LOCAL_P3_PASS_REQUEST_PENDING',CPU_checks=62,request_sha256=qh,archive=rec(arc))))
