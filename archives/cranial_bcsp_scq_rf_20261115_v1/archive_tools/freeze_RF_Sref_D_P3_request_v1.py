"""Freeze the authorized local Sref_D implementation and a pending, never executed request."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_Sref_D_implementation_20261114_v1'
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
ctx=read(O/'implementation_context_v1.json');q=copy.deepcopy(ctx['candidate']);mirror={k:Path(v) for k,v in ctx['mirror'].items()};parent=ctx['parent_C_request']
entry=O/'bcsp_scq_rf_Sref_D_training_entry_v1.py';test=O/'test_RF_Sref_D_entry_cpu_v1.py';cpu_path=O/'cpu_Sref_D_batch_v1/result_v1.json';cpu=read(cpu_path);static=read(O/'static_review_v1.json')
assert cpu['status']=='RF_SREF_D_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==44
assert cpu['entry']==rec(entry)==static['entry'] and cpu['test']==rec(test) and cpu['bridge']['sha256']==q['implementation']['bridge']['sha256']
assert not (O/'cpu_Sref_D_batch_v1/failure_v1.json').exists() and (O/'cpu_Sref_D_batch_v1/policy_stderr.bin').stat().st_size==0
policy=read(O/'cpu_Sref_D_batch_v1/policy_stdout.bin');assert all(policy.values()) and policy['actual_runtime_source_loaded'] and policy['complete_source_load_order'] and policy['all15_source_traceback_lines']
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['real_payload_arrays_read']==0
oldpair=read(mirror[parent['pair_contract']['path']]);pair=read(O/'RF_six_run_contract_v2.json')
assert all(pair[k]==v for k,v in oldpair.items()) and set(pair)-set(oldpair)=={'FoldD','metadata_extension'}
assert all(pair['FoldD'][k]==q[k] for k in ['QC','order_plan','data_root'])
assert pair['metadata_extension']['parent_sha256']==parent['pair_contract']['sha256']
ready=read(O/'RF_FoldD_metadata_readiness_v1.json');assert ready['identity']==q['identity'] and ready['fold']=='D' and ready['current_server_checked'] is False and ready['fresh_reverification_required']
for r in [*q['implementation'].values(),q['initialization'],q['order_plan'],q['QC']['qualified_receipt']]:
 p=mirror[r['path']];assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes']
oldentry=mirror[parent['implementation']['entry']['path']];oldtree=ast.parse(oldentry.read_text(encoding='utf-8'));newtree=ast.parse(entry.read_text(encoding='utf-8'))
of={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,ast.FunctionDef)};nf={n.name:ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,ast.FunctionDef)}
unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','validate_admission','scq_geometry','dispatch_training','startup_read_records']
assert all(of[k]==nf[k] for k in unchanged) and static['source_read_roots_unchanged']
for r in q['continuation_evidence'].values():assert rec(mirror[r['path']])['sha256']==r['sha256']
p3=dict(status='RF_SREF_D_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=q['implementation']['bridge']['sha256'],native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=44,CPU=rec(cpu_path),test=rec(test),static=rec(O/'static_review_v1.json'),policy_stdout=rec(O/'cpu_Sref_D_batch_v1/policy_stdout.bin'),unchanged_parent_functions=unchanged,
 checks=dict(all44_CPU_checks_pass=True,full_D_authorize_and_C_asset_rejection=True,original_D_order_and_source_identity=True,all_C_trio_freezes_bound=True,versioned_matrix_preserves_C_and_science=True,current_frozen_identity_D_readiness_server_unverified=True,bridge_model_runtime_loss_unchanged=True,finite_source_guard_and_exception_traceback=True,SCQ_initialization_and_optimizer_groups_unchanged=True,no_GPU_or_server=True),
 limitations=cpu['limitations']+['No full native Mamba executed; inherited same-device RF admission is reused.','Fold D real NPZ payload hashes and server resource/asset readiness must be freshly verified before a separately authorized run.','Finite SSM gradient non-bitwise reproducibility remains disclosed.'],server_operations=0,training=False,CUDA=False)
emit(O/'training_entry_P3_v1.json',p3)
T=O/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
for p in [entry,test,O/'static_review_v1.json',O/'training_entry_P3_v1.json',O/'RF_six_run_contract_v2.json',O/'RF_FoldD_metadata_readiness_v1.json']:shutil.copyfile(p,P/p.name)
shutil.copyfile(cpu_path,P/'training_CPU_result_v1.json')
for name,r in q['continuation_evidence'].items():shutil.copyfile(mirror[r['path']],P/(name+'_formal_freeze_v1.json'))
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False;q['P3']=rec(P/'training_entry_P3_v1.json',C+'/training_entry_P3_v1.json');q['CPU_evidence']=rec(P/'training_CPU_result_v1.json',C+'/training_CPU_result_v1.json')
q['activation_prerequisites'][2]='Verify uploaded archive+3 sidecars; all11 new targets/control/output absent; exclusive installation, current frozen identity and exact reused sources plus FoldD metadata, no overwrite.'
q['training_reference']='Fourth run of frozen matrix: scratch S-ref_D, no RF head, no checkpoint warmstart; original FoldD source/QC/order and same seed0/science/resources; C loss never changes D settings.'
# New metadata are packaged, not mistakenly required as already installed reused files.
packaged={C+'/'+p.name for p in P.iterdir()}
bindings={r['path']:r for r in q['reused_readonly_bindings'] if r['path'] not in packaged}
for r in [*[v for k,v in q['implementation'].items() if k!='entry'],q['initialization'],q['QC']['qualified_receipt'],q['QC']['verification'],*q['QC']['manifests'].values(),q['QC']['fold_binding'],q['order_plan']]:
 if r['path'] in bindings:assert bindings[r['path']]==r
 else:bindings[r['path']]=r
q['reused_readonly_bindings']=list(bindings.values())
request=P/'SCQ_RF_Sref_D_training_execution_request_v1.json';emit(request,q);qh=rec(request)['sha256']
mirror[q['P3']['path']]=P/'training_entry_P3_v1.json';mirror[q['CPU_evidence']['path']]=P/'training_CPU_result_v1.json';mirror[q['launch_contract']['request_path']]=request
spec=importlib.util.spec_from_file_location('Sref_D_final_metadata_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
x=e.exact;e.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
sm=e.source_module
def mod(name,r):
 m=sm(name,r)
 if name=='bcsp_training_contract_v1':
  ex=m.exact;m.exact=lambda r:ex(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else ex(r)
 return m
e.source_module=mod
a=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='MEMORY_ONLY_FINAL_CONTRACT_REVIEW_NOT_USER_AUTHORIZATION')
rt=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
bd=e.bound;e.bound=lambda r:a if r['path']=='MEMORY_AUTH' else rt if r['path']=='MEMORY_RUNTIME' else bd(r)
sys.modules.pop('bcsp_training_contract_v1',None)
v=e.authorize(rec(request,q['launch_contract']['request_path']),dict(path='MEMORY_AUTH',bytes=0,sha256='a'*64),dict(path='MEMORY_RUNTIME',bytes=0,sha256='b'*64))
assert len(v[3])==315 and v[1]['counts']['updates']==3900 and v[2].canonical_sha(v[5])=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838'
launcher=e.render_launcher(q,qh,'a'*64,'b'*64);assert launcher.index('mkdir -p')<launcher.index(' >') and max(len(l.encode()) for l in launcher.splitlines())<=2048
for key in ['science','identity','resources','initialization','static_config','admission','dependencies','environment','model_root','preflight_scope']:assert q[key]==parent[key]
for key,r in parent['implementation'].items():
 if key!='entry':assert q['implementation'][key]==r
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=C,files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'])
assert len(mapping['files'])==11;emit(T/'installation_mapping_v1.json',mapping)
arc=T/'bcsp_scq_rf_Sref_D_pending_20261114_v1.tar.gz'
with arc.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as t:
 members=t.getmembers();assert len(members)==12 and all(m.isfile() for m in members)
 listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
 with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'final_authorize_review_v1.json',dict(status='SREF_D_FINAL_AUTHORIZE_LAUNCHER_CONTRACT_PASS',request=rec(request),CPU_checks=44,selected_cases=315,full_order_batches=3900,common_state=v[-1],original_D_order_canonical=v[2].canonical_sha(v[5]),controls_materialized=False,server_operations=0))
emit(O/'final_local_mirror_v1.json',{k:str(v.resolve()) for k,v in mirror.items()})
emit(O/'delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),mapping=rec(T/'installation_mapping_v1.json'),P3=rec(O/'training_entry_P3_v1.json'),CPU_checks=44,install_files=11,archive_members=12,controls_materialized=False,server_operations=0,training=False,CUDA=False))
print(json.dumps(dict(status='SREF_D_LOCAL_P3_PASS_REQUEST_PENDING',CPU_checks=44,request_sha256=qh,archive=rec(arc))))
