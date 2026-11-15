"""Local post-implementation review and immutable pending Static_C request/delivery."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys,tarfile
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1'
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)
ctx=read(O/'implementation_context_v1.json');q=copy.deepcopy(ctx['candidate']);mirror={k:Path(v) for k,v in ctx['mirror'].items()}
entry=O/'bcsp_scq_rf_Requery_C_training_entry_v1.py';bridge=O/'bcsp_scq_rf_Requery_C_training_bridge_v1.py';test=O/'test_RF_Requery_C_entry_cpu_v1.py';cpu_path=O/'cpu_requery_entry_batch_v1/result_v1.json';cpu=read(cpu_path);static=read(O/'static_review_v1.json')
assert cpu['status']=='RF_REQUERY_C_ENTRY_ARTIFICIAL_CPU_PASS' and cpu['count']==len(cpu['checks'])==49
assert cpu['entry']==rec(entry)==static['entry'] and cpu['bridge']==rec(bridge)==static['bridge'] and cpu['test']==rec(test)
assert not (O/'cpu_requery_entry_batch_v1/failure_v1.json').exists()
policy=read(O/'cpu_requery_entry_batch_v1/policy_stdout.bin');assert all(policy.values()) and policy['all17_source_traceback_lines'] and policy['complete_source_load_order'] and policy['original_exception_preserved']
assert (O/'cpu_requery_entry_batch_v1/policy_stderr.bin').stat().st_size==0
assert cpu['optimizer_steps']==cpu['CUDA_calls']==cpu['server_operations']==cpu['checkpoint_loads']==cpu['real_payload_arrays_read']==0
for r in [*q['implementation'].values(),q['initialization'],q['rf_initialization']]:
 p=mirror[r['path']];assert p.stat().st_size==r['bytes'] and rec(p)['sha256']==r['sha256']
admission=read(mirror[q['admission']['construction']['path']]);assert admission['models'][2]['phase']=='Requery_eval1' and admission['models'][2]['parameters']==40827847 and admission['models'][2]['shared_initial_state_SHA256']==ctx['expected_common']
for p in [entry,bridge,test]:ast.parse(p.read_text(encoding='utf-8'))
old=R/'outputs/scq_rf_Static_C_implementation_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py'
oldtree=ast.parse(old.read_text(encoding='utf-8'));newtree=ast.parse(entry.read_text(encoding='utf-8'))
oldfunc={n.name:ast.dump(n,include_attributes=False) for n in oldtree.body if isinstance(n,ast.FunctionDef)};newfunc={n.name:ast.dump(n,include_attributes=False) for n in newtree.body if isinstance(n,ast.FunctionDef)}
unchanged=['require','no_links','sha','exact','bound','emit','source_module','payload_paths','geometry_record','render_launcher','make_budget','startup_read_records','validate_reference','validate_admission']
assert all(oldfunc[k]==newfunc[k] for k in unchanged) and static['source_read_roots_unchanged']
source=entry.read_text(encoding='utf-8')
assert source.index("timezone=source_module")<source.index('guard=cuda_entry.ExactSCQReads')<source.index('sys.addaudithook')
assert "factory=source_module('bcsp_scq_rf_factory_v1'" in source and 'startup_read_records(q)' in source
baseline=read(mirror[q['paired_baseline']['audit']['path']]);assert baseline['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and baseline['check_count']==26 and baseline['common_initial_state_SHA256']==ctx['expected_common']
p3=dict(status='RF_REQUERY_C_TRAINING_ENTRY_LOCAL_P3_PASS',entry_sha256=rec(entry)['sha256'],bridge_sha256=rec(bridge)['sha256'],native_admission_sha256=q['admission']['audit']['sha256'],CPU_checks=49,CPU=rec(cpu_path),test=rec(test),static=rec(O/'static_review_v1.json'),policy_stdout=rec(O/'cpu_requery_entry_batch_v1/policy_stdout.bin'),Sref_formal_freeze=q['paired_baseline']['audit'],
 checks=dict(all49_artificial_CPU_pass=True,complete_actual_RF_source_bridge_runtime_chain=True,exception_traceback_and_exact_read_guards=True,UTC_before_guard_preserved=True,both_frozen_byte_initializers=True,RF_formula_sources_and_runtime_unchanged=True,no_extra_optimizer_or_loss=True,shared_S_initialization_and_order_bound=True,four_added_RF_parameter_groups=True,Requery_N1_and_Q1_relative_geometry=True,Static_and_Sref_frozen_references=True,full_initial_state_match_required_before_native_training=True,fixed_changed_neighbor_fixture=True,full_loss_hooks_Q2_geometry_and_3900_counter=True,metadata_and_authorization_contract=True),
 unchanged_parent_functions=unchanged,limitations=cpu['limitations']+['Native 40,827,847 total validated against prior frozen CUDA construction; tiny CPU model validates exact 231,171 RF delta only.','Training resource trajectory and real data behavior unexecuted; fresh server readiness is mandatory.','Limited SSM gradient non-bitwise reproducibility remains disclosed.'],server_operations=0,training=False,CUDA=False,model_or_runtime_modifications=False)
sr=q['paired_static'];static_audit_path=mirror[sr['audit']['path']];static_audit=read(static_audit_path)
assert static_audit['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and static_audit['check_count']==34 and all(static_audit['checks'].values())
assert q['expected_full_initialization']==static_audit['initialization'] and static_audit['common_initial_state_SHA256']==ctx['expected_common']
p3['Static_formal_freeze']=sr['audit'];p3['expected_full_initialization']=q['expected_full_initialization']
emit(O/'training_entry_P3_v1.json',p3)
T=O/'pending_transport_v1';T.mkdir();P=T/'payload';P.mkdir()
sources=[entry,bridge,test,O/'training_entry_P3_v1.json',O/'static_review_v1.json']
for p in sources:shutil.copyfile(p,P/p.name)
shutil.copyfile(cpu_path,P/'training_CPU_result_v1.json');shutil.copyfile(mirror[q['paired_baseline']['audit']['path']],P/'Sref_C_formal_freeze_v1.json')
shutil.copyfile(static_audit_path,P/'Static_C_formal_freeze_v1.json')
q['paired_baseline']['audit']=rec(P/'Sref_C_formal_freeze_v1.json',C+'/Sref_C_formal_freeze_v1.json');mirror[q['paired_baseline']['audit']['path']]=P/'Sref_C_formal_freeze_v1.json'
q['paired_static']['audit']=rec(P/'Static_C_formal_freeze_v1.json',C+'/Static_C_formal_freeze_v1.json');mirror[q['paired_static']['audit']['path']]=P/'Static_C_formal_freeze_v1.json'
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False
q['P3']=rec(P/'training_entry_P3_v1.json',C+'/training_entry_P3_v1.json');q['CPU_evidence']=rec(P/'training_CPU_result_v1.json',C+'/training_CPU_result_v1.json')
q['activation_prerequisites'][2]='Verify uploaded archive+3 sidecars, all9 new targets/control/output absent, exact reused sources including admitted RF source files, both initializers and formal Sref reference evidence; no overwrite.'
q['training_reference']='Fresh from-scratch paired RF-Requery_C; never load Sref or Static final checkpoint; bind identical full initial parameter/buffer fingerprints. Preserve seed0, full shared S initialization, same315 cases, exact order and3900 updates.'
q['expected_parameters']=40827847;q['expected_RF_parameters']=231171
# Reuse is exact, finite and conflict-rejecting, including the new request's paired evidence.
bindings={r['path']:r for r in q['reused_readonly_bindings']}
for r in [*[v for k,v in q['implementation'].items() if k not in ('entry','bridge')],q['initialization'],q['rf_initialization'],*[v for k,v in q['paired_baseline'].items() if k!='audit'],*[v for k,v in q['paired_static'].items() if k!='audit']]:
 if r['path'] in bindings:assert bindings[r['path']]==r
 else:bindings[r['path']]=r
q['reused_readonly_bindings']=list(bindings.values())
request=P/'SCQ_RF_Requery_C_training_execution_request_v1.json';emit(request,q);qh=rec(request)['sha256']
mirror[q['P3']['path']]=O/'training_entry_P3_v1.json';mirror[q['CPU_evidence']['path']]=P/'training_CPU_result_v1.json';mirror[q['launch_contract']['request_path']]=request
spec=importlib.util.spec_from_file_location('Requery_C_final_metadata_only',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
x=e.exact;e.exact=lambda r:x(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else x(r)
sm=e.source_module
def mod(name,r):
 m=sm(name,r)
 if name=='bcsp_training_contract_v1':
  me=m.exact;m.exact=lambda r:me(dict(r,path=str(mirror[r['path']].resolve()))) if r['path'] in mirror else me(r)
 return m
e.source_module=mod
# Review the final authorize route with memory-only controls; these are not user execution receipts.
auth=dict(schema='bcsp-scq-rf-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='MEMORY_ONLY_FINAL_CONTRACT_REVIEW_NOT_EXECUTION_AUTHORIZATION')
runtime=dict(schema='bcsp-scq-rf-training-runtime-v1',request_sha256=qh,authorization_sha256='a'*64)
bd=e.bound;e.bound=lambda r:auth if r['path']=='MEMORY_AUTH' else runtime if r['path']=='MEMORY_RUNTIME' else bd(r)
sys.modules.pop('bcsp_training_contract_v1',None)
v=e.authorize(rec(request,q['launch_contract']['request_path']),dict(path='MEMORY_AUTH',bytes=0,sha256='a'*64),dict(path='MEMORY_RUNTIME',bytes=0,sha256='b'*64))
assert len(v[3])==315 and v[1]['counts']['updates']==3900 and v[-1]==ctx['expected_common']
launcher=e.render_launcher(q,qh,'a'*64,'b'*64);assert launcher.index('mkdir -p')<launcher.index(' >') and max(len(l.encode()) for l in launcher.splitlines())<=2048
parent=read(mirror[q['paired_baseline']['request']['path']])
for key in ['science','identity','resources','initialization','QC','order_plan','static_config','admission','dependencies','environment','pair_contract','data_root','model_root','preflight_scope']:assert q[key]==parent[key]
assert q['output']!=parent['output'] and q['launch_contract']['tmux_session']!=parent['launch_contract']['tmux_session']
static_request=read(mirror[q['paired_static']['request']['path']]);assert q['rf_initialization']==static_request['rf_initialization'] and q['output']!=static_request['output'] and q['launch_contract']['tmux_session']!=static_request['launch_contract']['tmux_session']
mapping=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request_sha256=qh,remote_root=C,files=[dict(member='payload/'+p.name,target=C+'/'+p.name,bytes=p.stat().st_size,sha256=rec(p)['sha256'],overwrite=False) for p in sorted(P.iterdir())],new_control_directory=C+'/control',new_output=q['output'],preconditions=q['activation_prerequisites'])
assert len(mapping['files'])==9;emit(T/'installation_mapping_v1.json',mapping)
arc=T/'bcsp_scq_rf_Requery_C_pending_20261114_v1.tar.gz'
with arc.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as t:
  t.add(T/'installation_mapping_v1.json',arcname='installation_mapping_v1.json',recursive=False)
  for p in sorted(P.iterdir()):t.add(p,arcname='payload/'+p.name,recursive=False)
with tarfile.open(arc) as t:
 members=t.getmembers();assert len(members)==10 and all(m.isfile() for m in members)
 listing=''.join(hashlib.sha256(t.extractfile(m).read()).hexdigest()+'  '+m.name+'\n' for m in members)
for suffix,text in [('.sha256',rec(arc)['sha256']+'  '+arc.name+'\n'),('.bytes',str(arc.stat().st_size)+'\n'),('.contents.sha256',listing)]:
 with Path(str(arc)+suffix).open('x',encoding='ascii') as f:f.write(text)
emit(O/'final_authorize_review_v1.json',dict(status='REQUERY_C_FINAL_AUTHORIZE_AND_LAUNCHER_CONTRACT_PASS',request=rec(request),CPU_checks=49,full_order_batches=3900,common_state=v[-1],same_science_and_resources=True,controls_materialized=False,server_operations=0))
emit(O/'final_local_mirror_v1.json',{k:str(v.resolve()) for k,v in mirror.items()})
emit(O/'delivery_v1.json',dict(status='AWAITING_UPLOAD_AND_SEPARATE_FULL_HASH_EXECUTION_AUTHORIZATION',request=rec(request),archive=rec(arc),mapping=rec(T/'installation_mapping_v1.json'),P3=rec(O/'training_entry_P3_v1.json'),CPU_checks=49,install_files=9,archive_members=10,controls_materialized=False,server_operations=0,training=False,CUDA=False))
print(json.dumps(dict(status='REQUERY_C_LOCAL_P3_PASS_REQUEST_PENDING',CPU_checks=49,request_sha256=qh,archive=rec(arc))))
