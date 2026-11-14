"""Exact authorized deployment and ONE tmux launch. No retry, no model preflight."""
import hashlib,json,os,shlex,shutil,socket,subprocess,sys,tarfile,time
from pathlib import Path
QH='f1a222d9268adf33ffc32127bb62ad82c6b6cdf20748b0a68e8f2c1b97f13431'
AH='cb3c196c3620715dd068e23f4a002d032842fdde69da9dbfceb2e9df56d862a8'
PROJECT=Path('/home/jovyan/adapointr_work/PoinTr')
ARCHIVE=Path('/home/jovyan/bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz')
INSTALL=PROJECT/'third_party/bcsp_f0_CD_native_prediction_20261111_v2'
START=time.monotonic();READ=0;PHASE='start';ROWS=[]

def need(ok,message):
 if not ok:raise RuntimeError(message)
def clean(path):
 p=Path(path);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'linked/nonabsolute: '+str(p))
 need(p==PROJECT or PROJECT in p.parents or p.parent==Path('/home/jovyan') or str(p).startswith('/opt/conda/envs/adapointr-mamba/') or p==Path('/usr/share/zoneinfo/Etc/UTC'),'unbound path: '+str(p));return p
def exact(r):
 global READ
 p=clean(r['path']);before=p.stat();need(p.is_file() and before.st_size==r['bytes'],'file type/size: '+str(p));h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   READ+=len(b);need(READ<=2147483648 and time.monotonic()-START<=120,'readiness hash/time budget');h.update(b)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'content drift: '+str(p))
 need(h.hexdigest()==r['sha256'],'hash mismatch: '+str(p));ROWS.append(r);return p
def sha(p):return hashlib.sha256(clean(p).read_bytes()).hexdigest()
def emit(path,value):
 with clean(path).open('x',encoding='ascii') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def phase(name):
 global PHASE
 PHASE=name;print(json.dumps(dict(phase=name,seconds=time.monotonic()-START,hashed_bytes=READ)),flush=True)
def smi(I):
 raw=subprocess.check_output(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=10,text=True).strip().splitlines();need(len(raw)==1,'one physical GPU');r=[x.strip() for x in raw[0].split(',')]
 need(r[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(r[4])<=256,'GPU identity/idle');return r
def absent_session(name):need(subprocess.run(['tmux','has-session','-t',name],capture_output=True,timeout=5).returncode==1,'tmux session present/unknown')

def main():
 phase('identity_and_uploaded_frozen_package')
 need(socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000,'current container')
 exact(dict(path=str(ARCHIVE),bytes=68663,sha256=AH))
 for r in SIDECARS:exact(r)
 need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0]==AH and int(Path(str(ARCHIVE)+'.bytes').read_text())==68663,'archive sidecars')
 payload={}
 with tarfile.open(ARCHIVE,'r:gz') as tar:
  members=tar.getmembers();need(len(members)==16,'sixteen members')
  for m in members:
   need(m.isfile() and m.size<1048576 and m.name not in payload and ((m.name.startswith('payload/') and Path(m.name).parts==('payload',Path(m.name).name)) or m.name=='installation_mapping_v2.json'),'archive member boundary')
   payload[m.name]=tar.extractfile(m).read()
 need(Path(str(ARCHIVE)+'.contents.sha256').read_text()==''.join(hashlib.sha256(payload[m.name]).hexdigest()+'  '+m.name+'\n' for m in members),'member listing')
 qb=payload['payload/F0_CD_native_prediction_execution_request_v2.json'];need(hashlib.sha256(qb).hexdigest()==QH,'authorized request')
 q=json.loads(qb);I=q['identity'];L=q['launch_contract'];out=clean(q['output']);mapping=json.loads(payload['installation_mapping_v2.json'])
 need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['forward_budget']==210 and q['limits']['wall_seconds']==7200,'scope')
 need(I['hostname']==socket.gethostname() and I['uid']==os.getuid() and I['project']==str(PROJECT) and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'Python/project identity')
 need(mapping['remote_root']==str(INSTALL) and len(mapping['files'])==15,'installation mapping')
 expected={}
 for r in mapping['files']:
  p=clean(r['target']);name='payload/'+p.name;need(p.parent==INSTALL and p.name not in expected and r['write_policy']=='EXCLUSIVE_CREATE_NO_OVERWRITE','target boundary')
  need(len(payload[name])==r['bytes'] and hashlib.sha256(payload[name]).hexdigest()==r['sha256'],'package member identity')
  expected[p.name]=dict(path=str(p),bytes=r['bytes'],sha256=r['sha256'])
 need(set(payload)=={'payload/'+n for n in expected}|{'installation_mapping_v2.json'},'exact target/member set')
 need(not clean(INSTALL).exists() and not out.exists() and INSTALL.parent.is_dir() and out.parent.is_dir(),'fresh installation/output parents')
 for r in expected.values():need(not clean(r['path']).exists(),'target already exists')
 absent_session(L['tmux_session']);gpu=smi(I);need(shutil.disk_usage(PROJECT).free>=q['limits']['minimum_free_disk_bytes'],'disk')
 phase('reused_sources_provider_and_extensions')
 rs=[q[k] for k in ['preflight_scope','static_config','numeric_policy','source_index','source_manifest','fold_binding','helper']]+list(q['implementation'].values())+q['dependencies'];seen=set()
 for r in rs:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 scope=json.loads(Path(q['preflight_scope']['path']).read_bytes());b=scope['bindings'];root=clean(q['model_root'])
 rs=[dict(path=str(root/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']) for r in b['candidate']]+[dict(path=str(root/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']) for r in b['isolated_model_project_sources']]+b['provider']+b['environment_metadata']
 for r in rs:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 need(sha(root/'base_model.yaml')==b['base_config']['sha256'],'base model config')
 link=Path('/usr/share/zoneinfo/UTC');need(link.is_symlink() and os.readlink(link)=='Etc/UTC' and str(link.resolve())=='/usr/share/zoneinfo/Etc/UTC','UTC exact link')
 exact(dict(path='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'))
 phase('two_checkpoints_and_210_exact_development_input_hashes')
 index=json.loads(payload['payload/'+Path(q['input_index']['path']).name]);need(len(index['runs'])==2 and len(index['inputs'])==210,'twofold210')
 for run in index['runs']:exact(run['checkpoint'])
 for row in index['inputs']:exact(row['input'])
 # Inert stdlib entry; reuse actual metadata validators, no model import or forward.
 namespace=dict(__name__='authorized_f0_metadata_only',__file__=q['entry']['path'])
 eb=payload['payload/'+Path(q['entry']['path']).name];exec(compile(eb,q['entry']['path'],'exec'),namespace)
 namespace['validate_index'](index,json.loads(Path(q['fold_binding']['path']).read_bytes()),json.loads(payload['payload/'+Path(q['selection']['path']).name]))
 namespace['validate_source'](index,json.loads(Path(q['source_index']['path']).read_bytes()),[json.loads(x) for x in Path(q['source_manifest']['path']).read_text().splitlines()])
 phase('all_readiness_pass_before_exclusive_install')
 need(not clean(INSTALL).exists() and not out.exists(),'target drift');smi(I);absent_session(L['tmux_session'])
 INSTALL.mkdir()
 for name,r in expected.items():
  with clean(r['path']).open('xb') as f:f.write(payload['payload/'+name]);f.flush();os.fsync(f.fileno())
  exact(r)
 control=INSTALL/'control';control.mkdir()
 emit(control/'readiness_and_installation_receipt_v2.json',dict(status='FIFTEEN_EXCLUSIVE_INSTALL_HASHES_PASS',request_sha256=QH,archive_sha256=AH,targets=list(expected.values()),read_manifest=ROWS,verification_seconds=time.monotonic()-START,checkpoint_files_hashed=2,development_input_files_hashed=210,arrays_decoded=0,checkpoint_deserialization=0,overwritten_files=0,identity=I,GPU_query=gpu))
 phase('materialize_one_way_authorization_runtime_launcher')
 auth=dict(schema='bcsp-development-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='User: 已上传至 /home/jovyan/，单独授权上述完整哈希。 Explicitly references '+QH+'; current zv9bqd-0; exclusive installation and ONE210 Native prediction, stop on failure, no retry/resume/preflight/training/BNCal/scoring.')
 emit(L['authorization'],auth);asha=sha(L['authorization'])
 emit(L['runtime'],dict(schema='bcsp-development-runtime-v1',request_sha256=QH,authorization_sha256=asha));rsha=sha(L['runtime'])
 def record(path):p=clean(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
 namespace['authorize'](record(L['request_path']),record(L['authorization']),record(L['runtime']))
 namespace['validate_evidence'](q,index)
 launcher=namespace['render_launcher'](q,QH,asha,rsha)
 with clean(L['launcher']).open('xb') as f:f.write(launcher.encode('utf-8'));f.flush();os.fsync(f.fileno())
 os.chmod(L['launcher'],0o700);subprocess.run(['/bin/bash','-n',L['launcher']],check=True,timeout=5)
 need(not out.exists() and time.monotonic()-START<=120,'last output/time gate');smi(I);absent_session(L['tmux_session'])
 emit(q['launch_attempt'],dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 phase('single_attempt_claimed_before_tmux')
 result=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'-c',str(PROJECT),'/bin/bash '+shlex.quote(L['launcher'])],capture_output=True,timeout=10)
 need(result.returncode==0,'tmux failed: '+repr(result.stderr[:512]));time.sleep(2)
 live=subprocess.run(['tmux','has-session','-t',L['tmux_session']],capture_output=True,timeout=5).returncode==0
 receipt=dict(status='AUTHORIZED_SINGLE_LAUNCH_RETURNED_INSPECT_STARTUP',request_sha256=QH,tmux_returncode=result.returncode,session=L['tmux_session'],session_present=live,authorization_sha256=asha,runtime_sha256=rsha,launcher_sha256=sha(L['launcher']),output=str(out),exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,log_tail=Path(L['log']).read_text(errors='replace')[-5000:] if Path(L['log']).exists() else None)
 emit(control/'startup_receipt_v2.json',receipt);print(json.dumps(receipt),flush=True)

# Exact sidecar bindings are inserted locally before this one-shot operation is transported.
SIDECARS=[{'path': '/home/jovyan/bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.sha256', 'bytes': 122, 'sha256': 'd497f17bbcfaf8875d4af86ab23f8d4a1207fac20eecf84c28e351be14fb4692'}, {'path': '/home/jovyan/bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.bytes', 'bytes': 6, 'sha256': '8ed52bda111509070d0ac85361112fcc0f92d89538b629dd0cc64727d9c4915d'}, {'path': '/home/jovyan/bcsp_f0_CD_native_prediction_pending_20261111_v2.tar.gz.contents.sha256', 'bytes': 1760, 'sha256': '7e179185e6a73dd75a5b39a696886df8760d56dc0f6b77027e74cc6bdc39ef5b'}]
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  failure=dict(status='AUTHORIZED_OPERATION_FAILED_STOP_NO_RETRY',phase=PHASE,error=repr(exc),hashed_bytes=READ,seconds=time.monotonic()-START,installation_root_exists=INSTALL.exists())
  control=INSTALL/'control'
  if control.is_dir() and not (control/'operation_failure_v2.json').exists():emit(control/'operation_failure_v2.json',failure)
  print(json.dumps(failure),flush=True);raise
