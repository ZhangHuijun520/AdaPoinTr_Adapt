"""Local P3, immutable package and pending request only; no server calls."""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
R=Path(__file__).resolve().parent.parent;S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2';PARENT=S.parent
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
ctx=read(S/'context_v2.json');q=copy.deepcopy(ctx['candidate']);remote=ctx['remote_root'];mirror=dict(ctx['mirror'])
entry=S/'bcsp_scq_rf_sixmodel_native_predict_v2.py';test=S/'test_RF_input_path_cpu_v2.py';cpu=S/'CPU_contract_v2/result_v2.json';static=read(S/'static_review_v2.json');result=read(cpu)
assert result['status']=='RF_INPUT_PATH_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==len(set(result['checks']))==24 and not (cpu.parent/'failure_v2.json').exists()
assert result['entry']==rec(entry)==static['entry'] and result['test']==rec(test)
assert static['status']=='STATIC_S0_S1_PASS' and static['all_functions_and_classes_AST_identical'] and static['all_other_constants_AST_identical']
old=PARENT/'bcsp_scq_rf_sixmodel_native_predict_v1.py'
def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert nodes(old)==nodes(entry)
oldp3=read(PARENT/'implementation_P3_v1.json');oldcpu=read(PARENT/'artificial_cpu_batch_v1/result_v1.json')
assert oldcpu['checks_passed']==51 and oldcpu['status']=='RF_NATIVE_CPU_CONTRACT_PASS' and all(oldp3['checks'].values()) and oldcpu['entry']==rec(old)
assert result['inherited_CPU_result']==rec(PARENT/'artificial_cpu_batch_v1/result_v1.json') and result['inherited_P3']==rec(PARENT/'implementation_P3_v1.json')
p3=copy.deepcopy(oldp3);p3.update(entry_sha256=rec(entry)['sha256'],test_sha256=rec(test)['sha256'],CPU_checks=24,CPU_result=rec(cpu),inherited_CPU_checks=51,inherited_CPU_result=rec(PARENT/'artificial_cpu_batch_v1/result_v1.json'),inherited_P3=rec(PARENT/'implementation_P3_v1.json'),static_review=rec(S/'static_review_v2.json'),changed_functions=[],changed_constants=['INDEX_SHA','DATA_ROOTS'],all_production_function_class_AST_unchanged=True,input_path_resolution=rec(S/'input_path_resolution_v2.json'))
p3['checks'].update(path_only24_CPU_checks_pass=True,all630_occurrences_only_path_changed=True,all210_unique_path_hashes_readonly_verified=True,all_functions_AST_identical=True,old_roots_and_wrong_fold_hash_budget_denied=True,final_v2_authorize_path_tested=True)
p3['limitations']+=['Only24 path/authorization/metadata checks rerun; previous51 and630 artificial forwards inherited by exact AST/source preservation.','No server calls or arrays in this implementation; fresh server identity/input/asset/checkpoint checks are mandatory at activation.']
emit(S/'implementation_P3_v2.json',p3)
O=S/'pending_request_v2';O.mkdir();T=O/'payload';T.mkdir();mapping=[]
def stage(p,name=None):
 n=name or p.name;target=T/n;shutil.copyfile(p,target);r=dict(rec(target),path=remote+'/'+n);mirror[r['path']]=str(target)
 mapping.append(dict(member='payload/'+n,target=r['path'],bytes=r['bytes'],sha256=r['sha256'],overwrite=False));return r
for k,p in [('entry',entry),('input_index',S/'RF_sixmodel_input_index_v2.json'),('protocol',PARENT/'RF_sixmodel_native_scope_v1.json'),('P3',S/'implementation_P3_v2.json')]:q[k]=stage(p)
for p,name in [(test,None),(cpu,'CPU_contract_result_v2.json'),(S/'static_review_v2.json',None),(PARENT/'artificial_cpu_batch_v1/source_policy_stdout.bin','source_policy_result_v1.json')]:stage(p,name)
for label,r in list(q['training_audits'].items()):q['training_audits'][label]=stage(Path(mirror[r['path']]),'frozen_'+label+'_training_audit_v1.json')
q['path_resolution']=stage(S/'input_path_resolution_v2.json')
resolution=read(S/'input_path_resolution_v2.json');stage(Path(resolution['observation']['path']),'input_path_readonly_observation_v1.json')
stage(PARENT/'implementation_P3_v1.json','inherited_implementation_P3_v1.json');stage(PARENT/'artificial_cpu_batch_v1/result_v1.json','inherited_CPU_contract_result_v1.json')
numeric=Path(mirror[q['numeric_policy']['path']]);assert sha(numeric)==q['numeric_policy']['sha256'];q['numeric_policy']=stage(numeric)
q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION';q['execution_authorized']=False
q['entry_contract']=dict(frozen_run_order=['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D'],counts=dict(forward=630,loss=0,backward=0,optimizer=0,BNCal=0,warmup=0,TTA=0),unique_inputs=210,unique_sources=42,models_loaded_sequentially=True,GT_conditioning=False,postfilter=False,registration=False,extra_instrumentation_forward=False)
req=T/'SCQ_RF_sixmodel_native_prediction_execution_request_v2.json';emit(req,q);mirror[q['launch_contract']['request_path']]=str(req)
mapping.append(dict(member='payload/'+req.name,target=q['launch_contract']['request_path'],bytes=req.stat().st_size,sha256=sha(req),overwrite=False))
spec=importlib.util.spec_from_file_location('RF_prediction_freeze',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
index=read(S/'RF_sixmodel_input_index_v2.json');folds=read(R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/fold_binding.json');e.validate_index(index,folds)
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
mp=O/'installation_mapping_v2.json';emit(mp,dict(status='FROZEN_NOT_INSTALLED_REQUIRES_FRESH_READINESS',remote_root=remote,files=mapping,reused_readonly_bindings=reused,checkpoint_files=[r['checkpoint'] for r in index['runs']],unique_input_files=210,prediction_occurrences=630,new_control_directory=remote+'/control',output=q['output'],request_sha256=sha(req),no_overwrite=True,materialization_order='separate full-hash execution authorization -> receipt SHA -> runtime -> launcher -> exclusive attempt claim -> one tmux',unverified_remote_binary_bindings=remote_only))
archive=O/'bcsp_scq_rf_sixmodel_native_pending_20261115_v2.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(mp,mp.name)]
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tar:
  for p,n in members:
   b=p.read_bytes();ti=tarfile.TarInfo(n);ti.size=len(b);ti.mode=0o600;ti.mtime=0;tar.addfile(ti,io.BytesIO(b))
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
emit(O/'local_mirror_v2.json',mirror)
emit(O/'final_static_freeze_v2.json',dict(status='FINAL_FROZEN_REQUEST_LOCAL_VALIDATION_PASS',final_full_authorize_memory_only=True,final_real_frozen_metadata_validator=True,remote_binary_checks_not_executed=True,locally_verified_reused_records=verified,remote_only_records=remote_only,launcher_bytes_max=max(len(v.encode()) for v in template.splitlines()),request=rec(req),entry=rec(entry),P3=rec(S/'implementation_P3_v2.json'),actual_controls_materialized=False))
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rec(req),archive=rec(archive),installation_files=len(mapping),CPU_checks=24,inherited_CPU_checks=51,P3_status=p3['status'],forward_budget=630,unique_cases=210,unique_sources=42,authorized_controls_materialized=False,server_operations=0,GPU_calls=0,repeat_preflight=False,fresh_server_readiness_required=True)
emit(O/'delivery_receipt_v2.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
