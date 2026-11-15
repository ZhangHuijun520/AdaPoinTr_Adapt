"""Local identity/path-only rebind. No server operations or execution controls."""
import copy,hashlib,importlib.util,io,json,shutil,tarfile
from pathlib import Path,PurePosixPath
A=Path(__file__).resolve().parent;S=A.parent;OLD=S/'pending_request_v1';OLDT=OLD/'transport_payload'
QH='8c2f849a1e3cb9cfbaac5e501f09647fa0de894491501e0d0bd48e09b9e9ee03'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def read(p):return json.loads(p.read_bytes())
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
identity=read(A/'identity_result_v1.json');package=read(A/'package_result_v1.json');assets=read(A/'assets_result_v1.json');points=read(A/'points_result_v1.json')
assert identity['hostname']=='shu-common-25721452-notebook-zv9bqd-0' and identity['uid']==1000 and int(identity['GPU'][4])<=256 and identity['free_disk_bytes']>=4294967296
assert package['status']=='UPLOAD_AND_FRESH_TARGETS_PASS' and package['old_install_and_controls_absent'] and package['new_v2_roots_absent']
assert assets['status']=='REUSED_SOURCE_PROVIDER_DEPENDENCY_HASHES_PASS' and points['status']=='TWO_CHECKPOINT_AND_210_INPUT_IDENTITIES_PASS'
oldfile=OLDT/'F0_CD_native_prediction_execution_request_v1.json';assert sha(oldfile)==QH
old=read(oldfile);mapping=read(OLD/'installation_mapping_v1.json')
entry=S/'bcsp_f0_twofold_native_predict_v1.py';assert sha(entry)==old['entry']['sha256']==read(S/'implementation_P3_v1.json')['entry_sha256']
receipt=dict(status='NEW_CONTAINER_READONLY_RESOURCE_AND_FROZEN_ASSETS_PASS',date='2026-11-11',old_request=bind(oldfile),old_request_disposition='Stopped at hostname gate; no server installation/control/claim/forward; not executable against new identity',current_container=identity,upload_check=bind(A/'package_result_v1.json'),asset_check=bind(A/'assets_result_v1.json'),checkpoint_and_input_check=bind(A/'points_result_v1.json'),raw_evidence=[bind(A/(label+'_'+stream+'_v1.bin')) for label in ['identity','package','assets','points'] for stream in ['stdout','stderr']],asset_files_hashed=len(assets['records']),checkpoint_files=2,input_files=210,hashed_bytes=assets['hashed_bytes']+points['hashed_bytes'],server_writes=0,ML_imports=0,arrays_decoded=0,checkpoint_deserialization=0,forward_calls=0,GPU_preflight_calls=0)
emit(A/'resource_rebind_audit_receipt_v2.json',receipt)
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_native_prediction_20261111_v2';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_native_development_20261111_v2'
new=copy.deepcopy(old);oldroot=mapping['remote_root'];oldout=old['output']
def rebase(v):
 if isinstance(v,dict):return {k:rebase(x) for k,x in v.items()}
 if isinstance(v,list):return [rebase(x) for x in v]
 if isinstance(v,str):return v.replace(oldroot,remote).replace(oldout,output)
 return v
new=rebase(new);g=identity['GPU']
new['identity'].update(hostname=identity['hostname'],uid=identity['uid'],project=identity['project'],python_realpath=identity['python_realpath'],python_version=identity['python_version'],gpu_uuid=g[0],gpu_name=g[1],driver_version=g[2],nvidia_smi_memory_total_MiB=int(g[3]))
new['environment']['CUDA_VISIBLE_DEVICES']=g[0]
new['run_id']='F0_CD_native_development_20261111_v2';new['launch_contract']['tmux_session']='bcsp_f0_CD_native_eval_20261111_v2'
new['launch_contract']['request_path']=remote+'/F0_CD_native_prediction_execution_request_v2.json'
new['provenance'].update(current_server_rechecked=True,current_identity_source='Fresh read-only resource-rebind audit on confirmed zv9bqd-0',previous_request_sha256=QH,previous_request_not_launched=True,rebind_scope='Identity and run/control paths only; exact entry/model/provider/data/210 contracts unchanged',prior_GPU_admission_other_UUID_driver=True,current_device_native_forward_not_yet_validated=True,no_repeat_GPU_preflight=True)
supplement=dict(status='IDENTITY_AND_PATH_ONLY_REBIND_FROZEN_AWAITING_REQUEST_AUTHORIZATION',old_request_sha256=QH,new_identity=new['identity'],old_identity=old['identity'],new_run_id=new['run_id'],new_install_root=remote,new_output=output,new_tmux=new['launch_contract']['tmux_session'],unchanged=['Production entry SHA256','Model/factory/encoder/decoder/provider/dependency files','Two checkpoint identities and formal training audits','Input index/protocol/selection and210 forward budget','FP32/TF32 settings, zero loss/backward/optimizer/BNCal/warmup/TTA','All resource thresholds','All210 Q,20 context,10 trace and RNG/state requirements','Separate explicit execution authorization and fail stop/no retry'],risk='Prior native CUDA admission was on old UUID/driver. Read-only hash consistency does not prove current CUDA execution; per user no-repeat-preflight scope, first authorized Native forward will exercise current device. Stop on any error.',no_current_CUDA_or_performance_claim=True)
emit(A/'resource_rebind_supplement_v2.json',supplement)
T=A/'transport_payload';T.mkdir();newmapping=[]
def stage(p,name=None):
 n=name or p.name;t=T/n;shutil.copyfile(p,t);r=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));newmapping.append(dict(local=str(t.absolute()),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
for r in mapping['files']:
 p=Path(r['local']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
 if p.name not in [oldfile.name,'launcher_REVIEW_TEMPLATE_NOT_AUTHORIZED_v1.txt']:stage(p)
new['resource_rebind_audit']=stage(A/'resource_rebind_audit_receipt_v2.json');new['resource_rebind_supplement']=stage(A/'resource_rebind_supplement_v2.json')
spec=importlib.util.spec_from_file_location('rebind_f0_entry',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
template=e.render_launcher(new,'a'*64,'b'*64,'c'*64).replace('a'*64,'REQUEST_SHA256').replace('b'*64,'AUTHORIZATION_SHA256').replace('c'*64,'RUNTIME_SHA256')
tpl=A/'launcher_REVIEW_TEMPLATE_NOT_AUTHORIZED_v2.txt'
with tpl.open('x',encoding='utf-8',newline='\n') as f:f.write(template)
new['launch_contract']['review_template']=stage(tpl)
unchangedkeys=['schema','status','stage','variant','fold','seed','n_input','n_output','batch_size','forward_budget','unique_cases','loss_calls','backward','optimizer_steps','BNCal','warmup','TTA','model_root','static_config','preflight_scope','dependencies','limits','selection_registration_timing','numeric_policy','source_index','source_manifest','fold_binding','helper','implementation','prior_native_admission','expected_artifacts','not_authorized']
assert all(new[k]==old[k] for k in unchangedkeys)
assert {k:v for k,v in new['environment'].items() if k!='CUDA_VISIBLE_DEVICES'}=={k:v for k,v in old['environment'].items() if k!='CUDA_VISIBLE_DEVICES'}
for k in ['entry','input_index','protocol','selection','P3']:
 assert new[k]['sha256']==old[k]['sha256'] and new[k]['bytes']==old[k]['bytes']
req=T/'F0_CD_native_prediction_execution_request_v2.json';emit(req,new);rbind=bind(req)
newmapping.append(dict(local=str(req.absolute()),target=new['launch_contract']['request_path'],bytes=rbind['bytes'],sha256=rbind['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
fakeauth=dict(schema='bcsp-development-authorization-v1',request_sha256=rbind['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_MEMORY_REBIND_CHECK_NOT_EXECUTION_AUTHORIZATION')
fakeruntime=dict(schema='bcsp-development-runtime-v1',request_sha256=rbind['sha256'],authorization_sha256='f'*64)
original=e.bound;e.bound=lambda r:{'q':new,'a':fakeauth,'r':fakeruntime}[r['path']]
try:assert e.authorize(dict(path='q',sha256=rbind['sha256']),dict(path='a',sha256='f'*64),dict(path='r'))==new
finally:e.bound=original
emit(A/'rebind_delta_static_verification_v2.json',dict(status='IDENTITY_PATH_ONLY_REBIND_STATIC_PASS',unchanged_keys=unchangedkeys,production_entry_sha256=sha(entry),prior_CPU_P3_preserved=True,CPU_tests_rerun=False,final_request_memory_authorize_pass=True,server_operations_from_freezer=0,request=rbind,authorized_controls_created=False))
L=new['launch_contract'];emit(A/'installation_mapping_v2.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=newmapping,reused_exact_bindings={k:new[k] for k in ['identity','model_root','preflight_scope','static_config','numeric_policy','fold_binding','source_index','source_manifest','helper','implementation','dependencies']},checkpoints=mapping['checkpoints'],unique_input_files=210,not_materialized=[L['authorization'],L['runtime'],L['launcher'],new['launch_attempt'],output]))
archive=A/'bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(T.iterdir())]+[(A/'installation_mapping_v2.json','installation_mapping_v2.json')]
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz') as tar:
  for p,n in members:
   blob=p.read_bytes();i=tarfile.TarInfo(n);i.size=len(blob);i.mode=0o600;i.mtime=0;tar.addfile(i,io.BytesIO(blob))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
pending=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=rbind,archive=bind(archive),installation_files=len(newmapping),prior_CPU_contracts=42,CPU_P3_preserved=True,production_source_changed=False,forwards=210,real_forward_calls=0,server_files_written=0,authorization_runtime_launcher_materialized=False,repeat_preflight=False,old_request_sha256=QH,old_request_stopped_not_executed=True)
emit(A/'pending_request_receipt_v2.json',pending);print(json.dumps(pending,ensure_ascii=False,indent=2))
