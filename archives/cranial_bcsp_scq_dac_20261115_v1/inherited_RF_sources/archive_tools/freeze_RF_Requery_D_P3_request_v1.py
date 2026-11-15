"""Freeze local Requery_D entry, P3, and an explicitly pending single-run request."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1'
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
ctx=read(O/'implementation_context_v1.json');q=copy.deepcopy(ctx['candidate']);mirror={k:Path(v) for k,v in ctx['mirror'].items()}
entry=O/'bcsp_scq_rf_Requery_D_training_entry_v1.py';bridge=mirror[q['implementation']['bridge']['path']];test=O/'test_RF_Requery_D_entry_cpu_v1.py';cp=O/'cpu_requery_D_entry_batch_v1';cpu=read(cp/'result_v1.json');static=read(O/'static_review_v1.json')
assert cpu['status']=='RF_REQUERY_D_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==54
assert cpu['entry']==rec(entry)==static['entry'] and cpu['bridge']==rec(bridge) and cpu['test']==rec(test)
assert not (cp/'failure_v1.json').exists() and (cp/'policy_stderr.bin').stat().st_size==0
policy=read(cp/'policy_stdout.bin');assert all(policy.values()) and policy['all17_source_traceback_lines'] and policy['complete_source_load_order'] and policy['original_exception_preserved']
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['checkpoint_loads']==cpu['real_payload_arrays_read']==0
for r in [*q['implementation'].values(),q['initialization'],q['rf_initialization'],q['readiness'],q['pair_contract']]:
 p=mirror[r['path']];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes']
admission=read(mirror[q['admission']['construction']['path']]);assert admission['models'][2]['phase']=='Requery_eval1' and admission['models'][2]['parameters']==40827847 and admission['models'][2]['shared_initial_state_SHA256']==ctx['expected_common']
old=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1/bcsp_scq_rf_Requery_C_training_entry_v1.py'
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(old.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
newfunc={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(entry.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','validate_admission','scq_geometry','startup_read_records']
assert all(oldfunc[k]==newfunc[k] for k in unchanged) and static['source_read_roots_unchanged']
baseline=read(mirror[q['paired_baseline']['audit']['path']]);assert baseline['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and baseline['fold']=='D' and baseline['check_count']==30 and all(baseline['checks'].values())
initref=q['initialization_reference'];rf_audit=read(mirror[initref['audit']['path']]);rf_init=read(mirror[initref['initialization']['path']])
assert rf_audit['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and all(rf_audit['checks'].values())
assert q['expected_model_initialization']=={k:rf_init[k] for k in ['parameter_sha256','persistent_state_sha256','seed']}
pair=read(mirror[q['pair_contract']['path']]);assert all(pair['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root'])
assert pair['arm_order']==['Sref_C','Static_C','Requery_C','Sref_D','Requery_D','Static_D'] and 'paired_static' not in q and 'expected_full_initialization' not in q
p3=dict(status='RF_REQUERY_D_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=rec(bridge)['sha256'],native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=54,CPU=rec(cp/'result_v1.json'),test=rec(test),static=rec(O/'static_review_v1.json'),policy_stdout=rec(cp/'policy_stdout.bin'),Sref_D_formal_freeze=q['paired_baseline']['audit'],RF_initialization_reference=initref,expected_model_initialization=q['expected_model_initialization'],unchanged_parent_functions=unchanged,
 checks=dict(all54_CPU_pass=True,D_only_authorize_rejects_C_assets=True,Sref_D_and_C_trio_freezes_bound=True,no_nonexistent_Static_D_prerequisite=True,model_initialization_separate_from_D_order=True,RF_source_bridge_runtime_unchanged=True,actual_RF_requery_gradients_and_geometric_logging=True,full_source_policy_and_traceback=True,both_frozen_initialization_bytes=True,all8_SCQ_RF_parameter_groups=True,full_loss_and3900_guards=True,no_GPU_or_server=True),
 limitations=cpu['limitations']+['Native 40,827,847 total and native Mamba path rely on the existing frozen CUDA admission; not rerun.','C RF model fingerprints describe shared initialization only; D batch order is independently frozen and checked.','Current server resources and exact D payload hashes still require fresh checks under separate execution authorization.'],server_operations=0,training=False,CUDA=False)
emit(O/'training_entry_P3_v1.json',p3)
T=O/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
for p in [entry,test,O/'static_review_v1.json',O/'training_entry_P3_v1.json']:shutil.copyfile(p,P/p.name)
shutil.copyfile(cp/'result_v1.json',P/'training_CPU_result_v1.json')
shutil.copyfile(mirror[q['paired_baseline']['audit']['path']],P/'Sref_D_formal_freeze_v1.json')
q['paired_baseline']['audit']=rec(P/'Sref_D_formal_freeze_v1.json',C+'/Sref_D_formal_freeze_v1.json');mirror[q['paired_baseline']['audit']['path']]=P/'Sref_D_formal_freeze_v1.json'
for name,r in list(q['continuation_evidence'].items()):
 p=P/(name+'_formal_freeze_v1.json');shutil.copyfile(mirror[r['path']],p);q['continuation_evidence'][name]=rec(p,C+'/'+p.name);mirror[C+'/'+p.name]=p
assert q['initialization_reference']['audit']['sha256']==q['continuation_evidence']['Static_C']['sha256']
q['initialization_reference']['audit']=q['continuation_evidence']['Static_C']
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False;q['P3']=rec(P/'training_entry_P3_v1.json',C+'/training_entry_P3_v1.json');q['CPU_evidence']=rec(P/'training_CPU_result_v1.json',C+'/training_CPU_result_v1.json')
q['activation_prerequisites'][2]='Verify uploaded archive+3 sidecars and all10 new targets/control/output absent; exclusive install only; exact original Requery bridge, admitted RF/source/init files, D QC/order and frozen references.'
q['training_reference']='Fifth frozen run: Requery_D before Static_D, scratch seed0, sameD315/order3900/resources; no checkpoint warmstart. Model initial fingerprints are shared RF provenance, not a C batch-order binding.'
bindings={r['path']:r for r in q['reused_readonly_bindings']}
for r in [*[v for k,v in q['implementation'].items() if k!='entry'],q['initialization'],q['rf_initialization'],q['readiness'],q['pair_contract'],q['order_plan'],q['QC']['qualified_receipt'],q['QC']['verification'],*q['QC']['manifests'].values(),q['QC']['fold_binding'],*[v for k,v in q['paired_baseline'].items() if k!='audit'],*[v for k,v in q['initialization_reference'].items() if k!='audit']]:
 if r['path'] in bindings:assert bindings[r['path']]==r
 else:bindings[r['path']]=r
q['reused_readonly_bindings']=list(bindings.values())
request=P/'SCQ_RF_Requery_D_training_execution_request_v1.json';emit(request,q);qh=rec(request)['sha256']
mirror[q['P3']['path']]=P/'training_entry_P3_v1.json';mirror[q['CPU_evidence']['path']]=P/'training_CPU_result_v1.json';mirror[q['launch_contract']['request_path']]=request
spec=importlib.util.spec_from_file_location('Requery_D_final_metadata_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
x=e.exact;e.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
sm=e.source_module
def mod(name,r):
 m=sm(name,r)
 if name=='bcsp_training_contract_v1':
  ex=m.exact;m.exact=lambda r:ex(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else ex(r)
 return m
e.source_module=mod
a=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='MEMORY_ONLY_FINAL_CONTRACT_REVIEW_NOT_USER_AUTHORIZATION');rt=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
bd=e.bound;e.bound=lambda r:a if r['path']=='MEMORY_AUTH' else rt if r['path']=='MEMORY_RUNTIME' else bd(r)
sys.modules.pop('bcsp_training_contract_v1',None)
v=e.authorize(rec(request,q['launch_contract']['request_path']),dict(path='MEMORY_AUTH',bytes=0,sha256='a'*64),dict(path='MEMORY_RUNTIME',bytes=0,sha256='b'*64))
assert len(v[3])==315 and v[-1]==ctx['expected_common'] and v[2].canonical_sha(v[5])=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
launcher=e.render_launcher(q,qh,'a'*64,'b'*64);assert launcher.index('mkdir -p')<launcher.index(' >') and max(len(l.encode()) for l in launcher.splitlines())<=2048
parent=ctx['parent_Sref_D_request']
for key in ['science','identity','resources','initialization','QC','order_plan','static_config','admission','dependencies','environment','pair_contract','data_root','model_root','preflight_scope','readiness']:assert q[key]==parent[key]
assert q['rf_initialization']==ctx['parent_C_request']['rf_initialization']
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=C,files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'])
assert len(mapping['files'])==10;emit(T/'installation_mapping_v1.json',mapping)
arc=T/'bcsp_scq_rf_Requery_D_pending_20261115_v1.tar.gz'
with arc.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as t:
 members=t.getmembers();assert len(members)==11 and all(m.isfile() for m in members)
 listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
 with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'final_authorize_review_v1.json',dict(status='REQUERY_D_FINAL_AUTHORIZE_LAUNCHER_CONTRACT_PASS',request=rec(request),CPU_checks=54,full_order_batches=3900,D_order_canonical=v[2].canonical_sha(v[5]),common_state=v[-1],no_Static_D_dependency=True,controls_materialized=False,server_operations=0))
emit(O/'final_local_mirror_v1.json',{k:str(v.resolve()) for k,v in mirror.items()})
emit(O/'delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),mapping=rec(T/'installation_mapping_v1.json'),P3=rec(O/'training_entry_P3_v1.json'),CPU_checks=54,install_files=10,archive_members=11,controls_materialized=False,server_operations=0,training=False,CUDA=False))
print(json.dumps(dict(status='REQUERY_D_LOCAL_P3_PASS_REQUEST_PENDING',CPU_checks=54,request_sha256=qh,archive=rec(arc))))
