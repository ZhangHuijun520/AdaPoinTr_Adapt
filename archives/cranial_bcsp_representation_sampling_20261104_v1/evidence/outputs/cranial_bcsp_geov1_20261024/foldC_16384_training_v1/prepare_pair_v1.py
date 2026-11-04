"""Prepare only the frozen Fold C 16k arm; no model import or server execution."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,io,json,math,struct,sys,tarfile,zipfile
N=Path(__file__).resolve().parent;B=N.parent
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
CODE=PROJECT+'/third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
DATA=PROJECT+'/data/bcsp_geov1_foldc_16384_seed0_v1'
CONTROL=CODE+'/control_train_foldC_16384_v1'
OUT=PROJECT+'/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1'
RUN='bcsp_geov1_b0_foldC_in16384_out8192_seed0_train_v1'
def raw(p):return Path(p).read_bytes()
def sha(r):return hashlib.sha256(r).hexdigest()
def load(p):return json.loads(raw(p))
def dump(name,d):
 p=N/name
 with p.open('x',encoding='ascii',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=True,allow_nan=False);f.write('\n')
 return p
def bind(p,remote=None):
 r=dict(path=str(Path(p).absolute()),bytes=len(raw(p)),sha256=sha(raw(p)))
 if remote:r['future_server_path']=remote
 return r
def server(p,path):return dict(path=path,bytes=len(raw(p)),sha256=sha(raw(p)))

q=load(P/'training_entry_request_v4.json')
parent_audit=load(P/'freeze_audit_v1/audit_report_v1.json')
assert parent_audit['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS'
assert sha(raw(P/'freeze_audit_v1/audit_report_v1.json'))=='8c7eabba742d5eda2853da437c9df55380f9d0802a8da165d9351dfc898307bf'
resources=load(N/'resources_observation_v1.json');assets=load(N/'assets_observation_v1.json');fresh=load(N/'freshness_observation_v1.json')
assert resources['hostname']==q['identity']['hostname'] and resources['uid']==1000
gpu=[x.strip() for x in resources['gpu']['stdout'].strip().split(',')]
assert gpu[:4]==[q['identity']['gpu_uuid'],q['identity']['gpu_name'],q['identity']['driver_version'],'24564']
assert int(gpu[4])<=256 and not resources['compute_processes']['stdout'].strip() and resources['disk']['free']>=4294967296
assert assets['parent_exit']=='0' and assets['parent_completion']['checkpoint_sha256']==parent_audit['checkpoint']['sha256']
assert fresh['tmux_returncode']==1 and all(not r['exists'] and r['parent_writable'] for r in fresh['paths'])
fold=load(B/'consolidated_binding_v1/fold_binding.json')['folds']['C']
ids=fold['train_case_ids'];assert len(ids)==len(set(ids))==315
manifests={n:{r['case_id']:r for r in map(json.loads,raw(B/('real_data_qc_v1/manifest_'+n+'.jsonl')).decode().splitlines())} for n in ['8192','16384']}
for n in manifests:assert sha(raw(B/('real_data_qc_v1/manifest_'+n+'.jsonl')))==q['QC']['manifests'][n]['sha256']
def npy(blob,shape):
 assert blob[:6]==b'\x93NUMPY';v=blob[6]
 assert v in (1,2,3)
 size=struct.unpack('<H' if v==1 else '<I',blob[8:10] if v==1 else blob[8:12])[0]
 start=10 if v==1 else 12;assert size<=4096
 header=ast.literal_eval(blob[start:start+size].decode('utf-8').strip())
 assert header==dict(descr='<f4',fortran_order=False,shape=shape)
 data=blob[start+size:];assert len(data)==math.prod(shape)*4
 return data
def arrays(path,record,n):
 assert not path.is_symlink() and path.resolve().is_relative_to((B/'real_data_qc_v1').resolve())
 before=path.stat();data=raw(path)
 assert len(data)<4194304 and sha(data)==record['sha256']
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  assert len(z.infolist())==2 and set(z.namelist())=={'partial.npy','implant.npy'}
  assert all(x.file_size<=262144 for x in z.infolist())
  partial=npy(z.read('partial.npy'),(n,3));target=npy(z.read('implant.npy'),(8192,3))
 assert (before.st_ino,before.st_size,before.st_mtime_ns)==(path.stat().st_ino,path.stat().st_size,path.stat().st_mtime_ns)
 assert sha(target)==record['target_array_sha256']
 return partial,target,len(data)
selected=[];total=0;case_rows=[]
for cid in ids:
 a=manifests['8192'][cid];b=manifests['16384'][cid]
 assert all(a[k]==b[k] for k in ['source_id','target_array_sha256','normalization','normalization_source','raw'])
 pa,ta,sa=arrays(B/'real_data_qc_v1'/a['point_path'],a,8192)
 pb,tb,sb=arrays(B/'real_data_qc_v1'/b['point_path'],b,16384)
 assert ta==tb and pa==pb[:8192*3*4]
 selected.append(b);total+=sb
 case_rows.append(dict(case_id=cid,source_id=b['source_id'],point_path=b['point_path'],bytes=sb,sha256=b['sha256'],target_array_sha256=sha(tb),target_bytes_equal=True,input8192_is_prefix=True))
pair=dump('paired315_data_verification_v1.json',dict(status='PASS_315_EXACT_TARGET_PREFIX_AND_PROVENANCE_PAIRS',train_cases=315,train_sources=63,
 target_points=8192,input_points=[8192,16384],payload_bytes_16384=total,all_targets_byte_identical=True,all8192_inputs_are_16384_prefixes=True,
 target_and_input_dtype='float32 little-endian C order',case_rows=case_rows,dev_payloads_read=0,confirmation_payloads_read=0,model_calls=0,data_regenerated=False))
qualified=load(B/'first_run_freeze_foldC_8192_v1/qualified_data_qc_foldC_8192_v1.json')
qualified['n_input']=16384;qualified['manifest_sha256']=q['QC']['manifests']['16384']['sha256']
qualified_path=dump('qualified_data_qc_foldC_16384_v1.json',qualified)
# Validate the existing reader against frozen metadata using an explicit local path map.
cp=P/'bcsp_training_contract_01dt08_v3.py'
spec=importlib.util.spec_from_file_location('bcsp_existing_metadata_contract_16k',cp);contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
local={q['QC']['verification']['path']:B/'real_data_qc_verification_v1.json',q['QC']['fold_binding']['path']:B/'consolidated_binding_v1/fold_binding.json'}
for n in ['8192','16384']:local[q['QC']['manifests'][n]['path']]=B/('real_data_qc_v1/manifest_'+n+'.jsonl')
def exact_local(r):
 p=local[r['path']];assert len(raw(p))==r['bytes'] and sha(raw(p))==r['sha256'];return p
contract.exact=exact_local
expected,records,spec=contract.bind_metadata(q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',16384)
assert expected==qualified and [r['case_id'] for r in records]==ids
T=B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2'
original=raw(T/'controller_template_v2.py').decode();text=original
changes=[("q['n_input'] == 8192","q['n_input'] == 16384"),("qualified['n_input'] == 8192","qualified['n_input'] == 16384"),
 ("q['QC']['manifests']['8192']","q['QC']['manifests']['16384']"),("r['n_input'] == r['n_target'] == 8192","r['n_input'] == 16384 and r['n_target'] == 8192"),
 ('payload_bytes == 49440750','payload_bytes == '+str(total))]
for old,new in changes:assert text.count(old)==1;text=text.replace(old,new)
template=N/'controller_template_foldC_16384_v1.py'
with template.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
tree=ast.parse(text)
predicates={x.args[1].value:x.args[0] for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='need' and len(x.args)==2 and isinstance(x.args[1],ast.Constant) and isinstance(x.args[1].value,str)}
def evaluate(name,values):return eval(compile(ast.Expression(predicates[name]),'<frozen_16k_metadata_predicate>','eval'),{},values)
testq=copy.deepcopy(q);testq['n_input']=16384
values=dict(q=testq,scope=dict(run_id=testq['run_id']),qualified=qualified,r=selected[0],counts={s:5 for s in fold['train_sources']},payload_bytes=total)
for name in ['single frozen run','qualified QC exact paths','training data metadata','fixed315 payload bytes/sources']:assert evaluate(name,values)
wrong=copy.deepcopy(values);wrong['q']['n_input']=8192;assert not evaluate('single frozen run',wrong)
wrong=copy.deepcopy(values);wrong['r']['n_target']=16384;assert not evaluate('training data metadata',wrong)
wrong=copy.deepcopy(values);wrong['payload_bytes']-=1;assert not evaluate('fixed315 payload bytes/sources',wrong)
p3=dump('minimal_16k_interface_P3_v1.json',dict(status='PASS_NO_PRODUCTION_SOURCE_CHANGE',controller_changes=[dict(old=a,new=b) for a,b in changes],
 existing_metadata_reader_accepts_16k=True,positive_actual_predicate_checks=4,negative_predicate_checks=3,
 model_entry_runtime_contract_provider_unchanged=True,new_CPU_model_tests=0,new_GPU_tests=0,template=bind(template),paired_data=bind(pair),
 existing_8k_initialization=assets['parent_initialization'],limitation='16k full training memory remains unmeasured; keep existing ceilings and stop on failure'))
q['n_input']=16384;q['run_id']=RUN;q['data_root']=DATA;q['output']=OUT;q['launch_attempt']=CONTROL+'/launch_attempt_v1.json'
q['QC']['qualified_receipt']=server(qualified_path,CODE+'/evidence/'+qualified_path.name)
qp=dump('training_entry_request_v1.json',q)
items=[]
for r in case_rows:items.append(dict(archive_member=r['point_path'],target=DATA+'/'+r['point_path'],bytes=r['bytes'],sha256=r['sha256'],local_file=str((B/'real_data_qc_v1'/r['point_path']).absolute())))
items.append(dict(archive_member='metadata/'+qualified_path.name,target=q['QC']['qualified_receipt']['path'],bytes=len(raw(qualified_path)),sha256=sha(raw(qualified_path)),local_file=str(qualified_path)))
mp=dump('minimal_installation_mapping_v1.json',dict(schema='bcsp-foldC-16384-data-installation-v1',status='PREPARED_NOT_DEPLOYED',expected_identity=q['identity'],project=PROJECT,data_root=DATA,
 directories=[DATA,DATA+'/points'],files=items,reused_code=q['implementation'],reused_static=q['static_config'],reused_order=q['order_plan'],
 rules=['Reverify identity,archive,mapped hashes,all316 targets absent,and safe parents before writing','Create only two listed directories;exclusive no-follow writes;no overwrite','After installation verify316 files before one training launch','Failure stops;no retry/resume/automatic cleanup']))
archive=N/'bcsp_foldC_16384_seed0_inputs_v1.tar.gz'
with archive.open('xb') as out:
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  for r in items:
   data=raw(r['local_file']);assert len(data)==r['bytes'] and sha(data)==r['sha256']
   info=tarfile.TarInfo(r['archive_member']);info.size=len(data);info.mode=0o644;info.mtime=0
   tf.addfile(info,io.BytesIO(data))
with (N/(archive.name+'.sha256')).open('x') as f:f.write(sha(raw(archive))+'  '+archive.name+'\n')
with (N/'bcsp_foldC_16384_seed0_inputs_v1.contents.sha256').open('x') as f:
 for r in items:f.write(r['sha256']+'  '+r['archive_member']+'\n')
outer=load(P/'training_execution_request_v4.json');oldout=outer['future_paths']['output']
oldcontrol=CODE+'/control_train_v3'
def rewrite(x):
 if isinstance(x,dict):return {k:rewrite(v) for k,v in x.items()}
 if isinstance(x,list):return [rewrite(v) for v in x]
 if isinstance(x,str):return x.replace(oldout,OUT).replace(oldcontrol,CONTROL).replace('bcsp_geov1_b0_foldc_in8192_seed0_train_v3','bcsp_geov1_b0_foldc_in16384_seed0_train_v1')
 return x
outer=rewrite(outer);outer['run_id']=RUN;outer['request_version']=1;outer['actual_training_attempt_index']=1
outer['future_paths']['execution_scope']=CONTROL+'/training_execution_scope_v1.json'
outer['request_kind']='Fold C paired16k input arm;one fresh scratch training after exclusive315NPZ+oneQC installation;no model/target/order/backend change'
outer['entry_request']=bind(qp,CONTROL+'/training_execution_request_v1.json')
outer['paired_8k_parent']=dict(run_id='bcsp_geov1_b0_foldC_in8192_out8192_seed0_train_v3',freeze_audit=bind(P/'freeze_audit_v1/audit_report_v1.json'),checkpoint_SHA256=parent_audit['checkpoint']['sha256'],checkpoint_used_for_initialization=False,
 expected_same_initialization=assets['parent_initialization'],post_training_requirement='Compare initial parameter,persistent-state and order fingerprints to8k before interpreting paired results')
outer['parent_evidence']=dict(current_resources=bind(N/'resources_observation_v1.json'),reused_assets=bind(N/'assets_observation_v1.json'),fresh_paths=bind(N/'freshness_observation_v1.json'),paired_data=bind(pair),minimal_interface_P3=bind(p3))
outer['scientific_contract']['input_points']=16384;outer['scientific_contract']['qualified_QC']=q['QC']['qualified_receipt']
outer['scientific_contract']['real_payload_scope']='315 exact Fold C training16k-input NPZ;no development/confirmation payloads;identical8192 target bytes and8192-prefix input pairing verified locally'
outer['resource_snapshot_evidence']=dict(UTC=resources['UTC'],GPU_memory_used_MiB=int(gpu[4]),compute_processes=0,disk_free_bytes=resources['disk']['free'],not_persistent_admission=True,recheck_before_launch=True,current_device_8k_training_passed=True,current_device_16k_full_training_unvalidated=True)
outer['future_materialization_contract']['authorization_schema']['request_sha256']=sha(raw(qp));outer['future_materialization_contract']['runtime_schema']['request_sha256']=sha(raw(qp))
argv=outer['future_materialization_contract']['external_training_argv'];argv[argv.index('--request-sha256')+1]=sha(raw(qp))
outer['prelaunch_guards'][1]='Verify frozen316-file data/QC installation and reused implementation/static/order/provider metadata;no broad inventory or downloads'
outer['previous_attempt']=dict(status='FIRST_ATTEMPT_FOR_THIS_16K_ARM',new_attempt_is_scratch=True,previous_8k_grants_reusable=False)
outer['known_failure_and_diagnostic_scope']=dict(PID_policy='DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',all_resource_thresholds_unchanged=True,full16k_training_fit_not_guaranteed=True,no_automatic_batch_reduction=True)
outer['minimal_deployment']=dict(status='PREPARED_NOT_DEPLOYED',installation_mapping=bind(mp),archive=bind(archive),future_upload_path='/home/jovyan/'+archive.name,
 full_scope_execution_authorization_covers='After manual upload,exclusive316-file installation and hash verification,then exactly one fresh16k tmux training attempt',failure_stops_before_training=True,installed_verification_required_before_controller=True)
outer['local_serialization']['controller_template']=bind(template)
outer['local_serialization']['future_rendering_contract'][0]='Only after a new fullSHA grant and verified16k installation,load raw finalscope,innerrequest,current-device risk record;validate exact hashes before rendering.'
outer['current_task_boundary']=dict(server_operations='Three bounded readonly probes;no server writes or CUDA',new_production_source=False,runtime_config_created=False,launcher_created=False,training_execution_authorization_created=False,training_steps=0)
outer['next']='Upload small data-only archive to/home/jovyan,then separately explicitly authorize this newfullSHA for exclusive installation and one16k training attempt;no execution now'
op=dump('training_execution_request_v1.json',outer)
with (N/'training_execution_request_v1.json.sha256').open('x') as f:f.write(sha(raw(op))+'  '+op.name+'\n')
print(json.dumps(dict(status='PREPARED_AWAITING_EXPLICIT_USER_AUTHORIZATION',paired_cases=315,payload_bytes=total,archive=bind(archive),request=bind(op),server_writes=0,training_started=False)))
