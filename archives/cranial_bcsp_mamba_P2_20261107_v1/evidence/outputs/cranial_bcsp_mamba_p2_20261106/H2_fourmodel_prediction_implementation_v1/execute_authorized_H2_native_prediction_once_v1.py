"""One authorized H2 four-model native prediction install/materialization/launch. No retries or resume."""
import hashlib,importlib.util,json,os,shlex,shutil,socket,subprocess,sys,tarfile,time
from pathlib import Path,PurePosixPath
QH='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170'
AH='69f9c1863250d7425471b4294726d0a278406d26565f496839207b0fcf9fbbcd'
ARCHIVE=Path('/home/jovyan/bcsp_p2_H2_fourmodel_native_prediction_pending_20261107_v1.tar.gz')
INSTALL=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_fourmodel_native_prediction_20261107_v1')
START=time.monotonic();PHASE='start';READ=0;ROWS=[]
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def clean(path):
 p=Path(path);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/path '+str(p));return p
def exact(r):
 global READ
 p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'],'type/size '+str(p));before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   READ+=len(b);need(READ<=6*1024**3 and time.monotonic()-START<=150,'verification read/time budget');h.update(b)
 after=p.stat();need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'read drift '+str(p));need(h.hexdigest()==r['sha256'],'hash '+str(p));ROWS.append(r);return p
def sha(p):return hashlib.sha256(clean(p).read_bytes()).hexdigest()
def emit(p,obj):
 with clean(p).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def stage(s):
 global PHASE
 PHASE=s;print(json.dumps(dict(phase=s,seconds=time.monotonic()-START,hashed_bytes=READ)),flush=True)
def smi(I):
 v=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().split(',')
 need([x.strip() for x in v[:4]]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
def absent(path):p=clean(path);need(not p.exists(),'target already exists '+str(p))
def main():
 stage('uploaded_archive_and_frozen_request')
 need(socket.gethostname()=='shu-common-25721452-notebook-1lvq9b-0' and os.getuid()==1000,'identity')
 exact(dict(path=str(ARCHIVE),bytes=74716,sha256=AH))
 need(clean(str(ARCHIVE)+'.sha256').read_text().split()==[AH,ARCHIVE.name] and int(clean(str(ARCHIVE)+'.bytes').read_text())==74716,'archive sidecars')
 payload={};listing=[]
 with tarfile.open(ARCHIVE,'r:gz') as t:
  members=t.getmembers();need(len(members)==12,'exact12 archive members')
  for m in members:
   need(m.isfile() and m.name not in payload and m.size<=8*1024**2,'member type/size/duplicate')
   rel=PurePosixPath(m.name);need(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix()==m.name,'member path')
   payload[m.name]=t.extractfile(m).read();listing.append(hashlib.sha256(payload[m.name]).hexdigest()+'  '+m.name+'\n')
 need(clean(str(ARCHIVE)+'.contents.sha256').read_text()==''.join(listing),'contents sidecar')
 request_name='H2_C_D_fourmodel_native_prediction_execution_request_v1.json';qb=payload['payload/'+request_name];need(hashlib.sha256(qb).hexdigest()==QH,'authorized request hash')
 q=json.loads(qb);I=q['identity'];L=q['launch_contract'];out=clean(q['output'])
 need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['schema']=='bcsp-p2-H2-fourmodel-native-prediction-v1' and q['forward_budget']==420 and q['batch_size']==1 and q['unique_cases']==210 and q['backward']==q['optimizer_steps']==q['BNCal']==q['loss_calls']==0,'420 Native-only contract')
 need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and Path(I['project']).resolve()==Path('/home/jovyan/adapointr_work/PoinTr'),'identity/project')
 os.chdir(clean(I['project']));need(str(Path.cwd())==I['project'],'working directory')
 mapping=json.loads(payload['installation_mapping_v1.json']);need(mapping['remote_root']==str(INSTALL) and mapping['status']=='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED' and len(mapping['files'])==11,'mapping')
 expected={}
 for r in mapping['files']:
  target=clean(r['target']);need(target.parent==INSTALL and r['write_policy']=='EXCLUSIVE_CREATE_NO_OVERWRITE' and target.name not in expected,'exclusive target mapping')
  b=payload['payload/'+target.name];need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'mapped bytes '+target.name)
  expected[target.name]=dict(path=str(target),bytes=r['bytes'],sha256=r['sha256'])
 need(set(payload)=={'installation_mapping_v1.json'}|{'payload/'+n for n in expected},'exact mapped members')
 need(expected[request_name]['sha256']==QH and L['request_path']==str(INSTALL/request_name),'request path')
 for r in [q['entry'],q['input_index'],q['protocol'],q['P3'],*q['implementation'].values(),q['static_config'],q['numeric_policy'],q['helper'],L['launcher_template'],*q['training_audits'].values()]:
  p=Path(r['path'])
  if p.parent==INSTALL:need(expected.get(p.name)==r,'request member binding '+str(p))
  else:exact(r)
 absent(INSTALL);absent(out);need(clean(INSTALL.parent).is_dir() and clean(out.parent).is_dir(),'existing safe parents')
 need(subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1,'tmux absent')
 smi(I);need(shutil.disk_usage(I['project']).free>=4294967296,'free disk')
 stage('reverify_fixed_assets_four_checkpoints_and210_inputs')
 idx=json.loads(payload['payload/'+Path(q['input_index']['path']).name]);protocol=json.loads(payload['payload/'+Path(q['protocol']['path']).name])
 need(len(idx['runs'])==4 and len(idx['inputs'])==420 and protocol['forward_budget']==420 and protocol['extra_intervention']['authorized'] is False,'4x105 native only')
 reused=[q['preflight_scope'],q['fold_binding'],q['source_index'],q['source_manifest'],q['numeric_policy'],q['static_config'],q['helper'],*q['implementation'].values(),*q['dependencies']]
 scope=json.loads(exact(q['preflight_scope']).read_bytes());bindings=scope['bindings'];modelroot=clean(q['model_root'])
 reused+=bindings['provider']+bindings['environment_metadata']
 for r in bindings['candidate']:reused.append(dict(path=str(modelroot/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['isolated_model_project_sources']:reused.append(dict(path=str(modelroot/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']))
 seen={r['path'] for r in ROWS}
 for r in reused:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 need(sha(modelroot/'base_model.yaml')==bindings['base_config']['sha256'],'base model config')
 for run in idx['runs']:
  need(run['mode'] in ('AUX','COUPLE') and run['fold'] in ('C','D') and len(run['dev_case_ids'])==105,'native run roles')
  exact(run['checkpoint'])
 unique={}
 for row in idx['inputs']:
  rec=row['input']
  if rec['path'] in unique:need(unique[rec['path']]==rec,'shared input binding drift')
  else:unique[rec['path']]=rec
 need(len(unique)==210,'210 exact shared input files')
 for r in unique.values():exact(r)
 version=subprocess.check_output([I['python_realpath'],'-I','-S','-B','-c','import sys;print(sys.version.split()[0])'],timeout=10,text=True).strip();need(version==I['python_version'],'Python version')
 stage('exclusive11_file_install')
 absent(INSTALL);absent(out);smi(I);INSTALL.mkdir()
 for name,r in expected.items():
  with clean(r['path']).open('xb') as f:f.write(payload['payload/'+name]);f.flush();os.fsync(f.fileno())
  exact(r)
 control=clean(INSTALL/'control');control.mkdir()
 emit(control/'readiness_and_installation_receipt_v1.json',dict(status='EXCLUSIVE_INSTALL_HASHES_PASS',request_sha256=QH,files=list(expected.values()),development_NPZ_byte_hashes=210,checkpoint_byte_hashes=4,NPZ_arrays_decoded=0,checkpoint_reads=0,read_manifest=ROWS,verification_seconds=time.monotonic()-START))
 stage('one_way_authorization_runtime_launcher')
 auth=dict(schema='bcsp-development-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='2026-11-07 user: 已上传，对上述完整哈希单独授权不覆盖安装与唯一一次训练。 Complete request SHA256 '+QH+'; H2 four-model420 Native prediction only, no condition intervention/scoring/training, no automatic retry/resume/evaluation/BNCal.')
 emit(L['authorization'],auth);authsha=sha(L['authorization']);emit(L['runtime'],dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=authsha));runtime_sha=sha(L['runtime'])
 template=exact(L['launcher_template']).read_text(encoding='utf-8');launch=template.replace('REQUEST_SHA256',QH).replace('AUTHORIZATION_SHA256',authsha).replace('RUNTIME_SHA256',runtime_sha)
 need(not any(p in launch for p in ['REQUEST_SHA256','AUTHORIZATION_SHA256','RUNTIME_SHA256']) and max(map(len,launch.splitlines()))<=2048,'render placeholders/line limit')
 with clean(L['launcher']).open('x',encoding='utf-8') as f:f.write(launch);f.flush();os.fsync(f.fileno())
 os.chmod(L['launcher'],0o700);subprocess.run(['/bin/bash','-n',L['launcher']],check=True,timeout=5)
 # Actual authorization path, standard-library metadata only, before any tmux/model execution.
 spec=importlib.util.spec_from_file_location('h2_authorized_training_entry',exact(q['entry']));entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
 record=lambda p,h:dict(path=p,bytes=Path(p).stat().st_size,sha256=h)
 validated=entry.authorize(expected[request_name],record(L['authorization'],authsha),record(L['runtime'],runtime_sha))
 need(validated==q,'actual request authorization')
 runs,rows=entry.validate_index(idx,entry.bound(q['fold_binding']))
 entry.validate_source(idx,entry.bound(q['source_index']),[json.loads(line) for line in exact(q['source_manifest']).read_text().splitlines()])
 entry.validate_evidence(q,idx)
 emit(control/'prelaunch_authorization_contract_v1.json',dict(status='ACTUAL_AUTHORIZE_INDEX_SOURCE_EVIDENCE_PASS',request_sha256=QH,models=4,development_rows=420,unique_cases=210,forward_budget=420,backward=0,loss_calls=0,optimizer_steps=0,model_constructed=False))
 stage('single_attempt_claim_and_tmux')
 absent(out);need(subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1,'last single-use gate');smi(I)
 emit(q['launch_attempt'],dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 r=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'-c',I['project'],'/bin/bash '+shlex.quote(L['launcher'])],capture_output=True,text=True,timeout=10);need(r.returncode==0,'tmux start '+r.stderr[:512]);time.sleep(3)
 live=subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
 status=dict(status='AUTHORIZED_SINGLE_LAUNCH_RETURNED',request_sha256=QH,tmux_returncode=r.returncode,session=L['tmux_session'],session_present=live,authorization_sha256=authsha,runtime_sha256=runtime_sha,launcher_sha256=sha(L['launcher']),output=str(out),exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,log_tail=Path(L['log']).read_text(errors='replace')[-4500:] if Path(L['log']).exists() else None)
 emit(control/'startup_receipt_v1.json',status);print(json.dumps(status,ensure_ascii=True),flush=True)
try:main()
except BaseException as exc:
 print(json.dumps(dict(status='AUTHORIZED_OPERATION_FAILED_STOP_NO_RETRY',phase=PHASE,error=repr(exc),hashed_bytes=READ,seconds=time.monotonic()-START,installation_root_exists=INSTALL.exists())),flush=True);raise
