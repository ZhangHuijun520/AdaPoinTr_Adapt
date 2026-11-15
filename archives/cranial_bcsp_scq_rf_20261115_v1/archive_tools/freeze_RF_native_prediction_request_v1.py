"""Local P3, immutable package and pending request only; no server calls."""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
ctx=read(S/'context_v1.json');q=copy.deepcopy(ctx['candidate']);remote=ctx['remote_root'];mirror=dict(ctx['mirror'])
entry=S/'bcsp_scq_rf_sixmodel_native_predict_v1.py';test=S/'test_RF_native_prediction_cpu_v1.py';cpu=S/'artificial_cpu_batch_v1/result_v1.json';static=read(S/'static_review_v1.json');result=read(cpu)
assert result['status']=='RF_NATIVE_CPU_CONTRACT_PASS' and result['checks_passed']==len(set(result['checks']))==len(result['checks'])==51
assert result['synthetic_forwards']==630 and result['actual_mother_artificial_full_forwards']==3 and not (cpu.parent/'failure_v1.json').exists()
assert result['entry']==rec(entry)==static['entry'] and result['test']==rec(test)==static['test']
for r in result['source_bindings']:assert rec(Path(r['path']))==r
policy=read(cpu.parent/'source_policy_stdout.bin');assert all(policy.values()) and static['status']=='STATIC_S0_S1_PASS' and all(static['checks'].values())
old=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2/bcsp_scq_fourmodel_native_predict_v2.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=nodes(old),nodes(entry);inherited=static['inherited_AST_unchanged'];assert all(a[n]==b[n] for n in inherited)
changed=[n for n in b if a.get(n)!=b[n]]
assert set(changed)=={'authorize','validate_index','validate_evidence','load_scq_builder','validate_scq_model','validate_model','build_scq_model','make_source_guard','scq_arrays','execute_pair','main'}
checks=dict(final_source_hashes_match_single51_CPU_batch=True,static_S0_S1_pass=True,actual_ten_source_loading_exact_policy_and_traceback_tested=True,source_write_and_neighbor_read_denied=True,both_frozen_initializers_bound=True,three_actual_mother_forwards_with_artificial_mixers=True,all_three_production_dispatch_signatures_tested=True,strict_artificial_checkpoint_positive_negative=True,complete_authorize_one_way_chain_tested=True,all630_artificial_outer_forwards_exact=True,RF_stage_equations_and_output_row_order_tested=True,no_extra_model_forward_or_full_trace=True,six_state_CPU_RNG_invariance_tested=True,first_failure_stops_without_next_model=True,inherited_numeric_resource_policy_unchanged=True,six_formal_training_audits_and_checkpoint_metadata_bound=True,unchanged_folds_input_hashes_D_only_normalization=True,accepted_cross_device_D_limitation_preserved=True,POSIX_parent_before_redirection=True,no_repeated_GPU_preflight=True)
p3=dict(status='LOCAL_RF_NATIVE_PREDICTION_P3_PASS',date='2026-11-15',entry_sha256=sha(entry),test_sha256=sha(test),CPU_checks=51,CPU_result=rec(cpu),static_review=rec(S/'static_review_v1.json'),actual_source_policy=policy,checks=checks,inherited_entry=rec(old),inherited_AST_unchanged=inherited,changed_functions=changed,CPU_runtime=dict(python='E:/RelocatedData/zhj/.conda/envs/adapointr/python.exe',torch='2.5.1+cpu'),limitations=['Three actual mother/factory forward paths used artificial grouper and causal mixers; no native CUDA or real checkpoint arrays loaded.','630 lightweight artificial forwards validate lifecycle only, not model accuracy.','Fresh current server identity, exact210 input paths/hashes, six checkpoint hashes, reuse assets and free disk remain mandatory activation checks.','D Static training uses different GPU UUID and driver; only supplementary device-confounded D comparison, C pair is primary same-device mechanism evidence.','Historical RF CUDA admission is not proof of current-device or prediction CUDA equivalence.','Sampled monitoring provides no hard resource isolation or PID namespace ownership guarantee.'],server_operations=0,GPU_calls=0,real_checkpoint_loads=0,real_payload_arrays=0,repeat_preflight=False)
emit(S/'implementation_P3_v1.json',p3)
O=S/'pending_request_v1';O.mkdir();T=O/'payload';T.mkdir();mapping=[]
def stage(p,name=None):
 n=name or p.name;target=T/n;shutil.copyfile(p,target);r=dict(rec(target),path=remote+'/'+n);mirror[r['path']]=str(target)
 mapping.append(dict(member='payload/'+n,target=r['path'],bytes=r['bytes'],sha256=r['sha256'],overwrite=False));return r
for k,p in [('entry',entry),('input_index',S/'RF_sixmodel_input_index_v1.json'),('protocol',S/'RF_sixmodel_native_scope_v1.json'),('P3',S/'implementation_P3_v1.json')]:q[k]=stage(p)
for p,name in [(test,None),(cpu,'CPU_contract_result_v1.json'),(S/'static_review_v1.json',None),(cpu.parent/'source_policy_stdout.bin','source_policy_result_v1.json')]:stage(p,name)
for label,path in ctx['audit_local_files'].items():q['training_audits'][label]=stage(Path(path),'frozen_'+label+'_training_audit_v1.json')
numeric=Path(mirror[q['numeric_policy']['path']]);assert sha(numeric)==q['numeric_policy']['sha256'];q['numeric_policy']=stage(numeric)
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False
q['entry_contract']=dict(frozen_run_order=['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D'],counts=dict(forward=630,loss=0,backward=0,optimizer=0,BNCal=0,warmup=0,TTA=0),unique_inputs=210,unique_sources=42,models_loaded_sequentially=True,GT_conditioning=False,postfilter=False,registration=False,extra_instrumentation_forward=False)
req=T/'SCQ_RF_sixmodel_native_prediction_execution_request_v1.json';emit(req,q);mirror[q['launch_contract']['request_path']]=str(req)
mapping.append(dict(member='payload/'+req.name,target=q['launch_contract']['request_path'],bytes=req.stat().st_size,sha256=sha(req),overwrite=False))
spec=importlib.util.spec_from_file_location('RF_prediction_freeze',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
index=read(S/'RF_sixmodel_input_index_v1.json');folds=read(R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/fold_binding.json');e.validate_index(index,folds)
assert e.INDEX_SHA==q['input_index']['sha256'] and e.PROTOCOL_SHA==q['protocol']['sha256'] and e.RF_INITIALIZATION==q['rf_initialization']
template=e.render_launcher(q,'a'*64,'b'*64,'c'*64);command=next(v for v in template.splitlines() if v.startswith('/usr/bin/timeout'));argv=shlex.split(command)
assert q['entry']['path'] in argv and q['launch_contract']['request_path'] in argv and '\\' not in command and max(len(v.encode()) for v in template.splitlines())<=2048 and template.index('mkdir -p --')<template.index(' >')
# Complete final request authorization path in memory only. No executable controls are written.
saved=e.bound;fake=dict(Q=q,A=dict(schema='bcsp-development-authorization-v1',request_sha256=sha(req),explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_MEMORY_ONLY_NOT_AUTHORIZATION'),R=dict(schema='bcsp-development-runtime-v1',request_sha256=sha(req),authorization_sha256='b'*64))
try:
 e.bound=lambda r:fake[r['path']]
 assert e.authorize(dict(path='Q',sha256=sha(req)),dict(path='A',sha256='b'*64),dict(path='R'))==q
finally:e.bound=saved
# Final real evidence validator, mapped to exact local byte copies; remote binary checks remain activation prerequisites.
orig=e.exact
try:
 e.exact=lambda r:orig(dict(r,path=mirror.get(r['path'],r['path'])))
 local=copy.deepcopy(q);local['dependencies']=[]
 e.validate_evidence(local,index)
finally:e.exact=orig
reused=[]
def visit(v):
 if isinstance(v,dict):
  if {'path','bytes','sha256'}<=set(v) and str(v['path']).startswith('/'):reused.append({k:v[k] for k in ['path','bytes','sha256']})
  else:
   for x in v.values():visit(x)
 elif isinstance(v,list):
  for x in v:visit(x)
visit({k:q[k] for k in ['implementation','initialization','rf_initialization','static_config','preflight_scope','dependencies','helper','fold_binding','source_manifest','prior_native_admission']})
reused=list({r['path']:r for r in reused}.values());verified=0;remote_only=[]
for r in reused:
 if r['path'] in mirror:
  p=Path(mirror[r['path']]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];verified+=1
 else:remote_only.append(r)
mp=O/'installation_mapping_v1.json';emit(mp,dict(status='FROZEN_NOT_INSTALLED_REQUIRES_FRESH_READINESS',remote_root=remote,files=mapping,reused_readonly_bindings=reused,checkpoint_files=[r['checkpoint'] for r in index['runs']],unique_input_files=210,prediction_occurrences=630,new_control_directory=remote+'/control',output=q['output'],request_sha256=sha(req),no_overwrite=True,materialization_order='separate full-hash execution authorization -> receipt SHA -> runtime -> launcher -> exclusive attempt claim -> one tmux',unverified_remote_binary_bindings=remote_only))
archive=O/'bcsp_scq_rf_sixmodel_native_pending_20261115_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(mp,mp.name)]
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tar:
  for p,n in members:
   b=p.read_bytes();ti=tarfile.TarInfo(n);ti.size=len(b);ti.mode=0o600;ti.mtime=0;tar.addfile(ti,io.BytesIO(b))
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
emit(O/'local_mirror_v1.json',mirror)
emit(O/'final_static_freeze_v1.json',dict(status='FINAL_FROZEN_REQUEST_LOCAL_VALIDATION_PASS',final_full_authorize_memory_only=True,final_real_frozen_metadata_validator=True,remote_binary_checks_not_executed=True,locally_verified_reused_records=verified,remote_only_records=remote_only,launcher_bytes_max=max(len(v.encode()) for v in template.splitlines()),request=rec(req),entry=rec(entry),P3=rec(S/'implementation_P3_v1.json'),actual_controls_materialized=False))
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rec(req),archive=rec(archive),installation_files=len(mapping),CPU_checks=51,P3_status=p3['status'],forward_budget=630,unique_cases=210,unique_sources=42,authorized_controls_materialized=False,server_operations=0,GPU_calls=0,repeat_preflight=False,fresh_server_readiness_required=True)
emit(O/'delivery_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
