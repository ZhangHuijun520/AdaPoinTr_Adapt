"""Exact authorized deployment and ONE tmux launch. No retry, no model preflight."""
import hashlib,json,os,shlex,shutil,socket,subprocess,sys,tarfile,time
from pathlib import Path
QH='d1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812'
AH='d8dfde92d514cb158393e6d32da39afaf8aacc7e27169225e0d716f1bf4f3bcd'
PROJECT=Path('/home/jovyan/adapointr_work/PoinTr')
ARCHIVE=Path('/home/jovyan/bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz')
INSTALL=PROJECT/'third_party/bcsp_lqi_cuda_20261111_v1'
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
 exact(dict(path=str(ARCHIVE),bytes=21023,sha256=AH))
 for r in SIDECARS:exact(r)
 need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0]==AH and int(Path(str(ARCHIVE)+'.bytes').read_text())==21023,'archive sidecars')
 payload={}
 with tarfile.open(ARCHIVE,'r:gz') as tar:
  members=tar.getmembers();need(len(members)==9,'sixteen members')
  for m in members:
   need(m.isfile() and m.size<1048576 and m.name not in payload and ((m.name.startswith('payload/') and Path(m.name).parts==('payload',Path(m.name).name)) or m.name=='installation_mapping_v1.json'),'archive member boundary')
   payload[m.name]=tar.extractfile(m).read()
 need(Path(str(ARCHIVE)+'.contents.sha256').read_text()==''.join(hashlib.sha256(payload[m.name]).hexdigest()+'  '+m.name+'\n' for m in members),'member listing')
 qb=payload['payload/LQI_artificial_cuda_execution_request_v1.json'];need(hashlib.sha256(qb).hexdigest()==QH,'authorized request')
 q=json.loads(qb);I=q['identity'];L=q['launch_contract'];out=clean(q['output']);mapping=json.loads(payload['installation_mapping_v1.json'])
 need(q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['science']['full_forward']==q['science']['full_loss']==q['science']['full_backward']==2 and q['science']['optimizer_steps']==0 and q['limits']['wall_seconds']==7200,'scope')
 need(I['hostname']==socket.gethostname() and I['uid']==os.getuid() and I['project']==str(PROJECT) and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'Python/project identity')
 need(mapping['remote_root']==str(INSTALL) and len(mapping['files'])==8,'installation mapping')
 expected={}
 for r in mapping['files']:
  p=clean(r['target']);name='payload/'+p.name;need(p.parent==INSTALL and p.name not in expected and r['overwrite'] is False,'target boundary')
  need(len(payload[name])==r['bytes'] and hashlib.sha256(payload[name]).hexdigest()==r['sha256'],'package member identity')
  expected[p.name]=dict(path=str(p),bytes=r['bytes'],sha256=r['sha256'])
 need(set(payload)=={'payload/'+n for n in expected}|{'installation_mapping_v1.json'},'exact target/member set')
 need(not clean(INSTALL).exists() and not out.exists() and INSTALL.parent.is_dir() and out.parent.is_dir(),'fresh installation/output parents')
 for r in expected.values():need(not clean(r['path']).exists(),'target already exists')
 absent_session(L['tmux_session']);gpu=smi(I);need(shutil.disk_usage(PROJECT).free>=q['limits']['minimum_free_disk_bytes'],'disk')
 phase('reused_sources_provider_and_extensions')
 rs=[q[k] for k in ['preflight_scope','static_config','helper','parent_helper','timezone_implementation']]+list(q['implementation'].values())+q['dependencies'];seen=set()
 for r in rs:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 scope=json.loads(Path(q['preflight_scope']['path']).read_bytes());b=scope['bindings'];root=clean(q['model_root'])
 rs=[dict(path=str(root/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']) for r in b['candidate']]+[dict(path=str(root/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']) for r in b['isolated_model_project_sources']]+b['provider']+b['environment_metadata']
 for r in rs:
  if r['path'] not in seen:exact(r);seen.add(r['path'])
 need(sha(root/'base_model.yaml')==b['base_config']['sha256'],'base model config')
 link=Path('/usr/share/zoneinfo/UTC');need(link.is_symlink() and os.readlink(link)=='Etc/UTC' and str(link.resolve())=='/usr/share/zoneinfo/Etc/UTC','UTC exact link')
 exact(dict(path='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'))
 phase('inert_exact_entry_contract_before_exclusive_install')
 namespace=dict(__name__='authorized_lqi_metadata_only',__file__=q['entry']['path'])
 eb=payload['payload/'+Path(q['entry']['path']).name];exec(compile(eb,q['entry']['path'],'exec'),namespace)
 artificial=dict(schema='bcsp-lqi-cuda-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='PREINSTALL_CONTRACT_REVIEW_ONLY')
 namespace['authorize'](q,QH,artificial,'a'*64,dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256=QH,authorization_sha256='a'*64))
 phase('all_readiness_pass_before_exclusive_install')
 need(not clean(INSTALL).exists() and not out.exists(),'target drift');smi(I);absent_session(L['tmux_session'])
 INSTALL.mkdir()
 for name,r in expected.items():
  with clean(r['path']).open('xb') as f:f.write(payload['payload/'+name]);f.flush();os.fsync(f.fileno())
  exact(r)
 control=INSTALL/'control';control.mkdir()
 emit(control/'readiness_and_installation_receipt_v1.json',dict(status='EIGHT_EXCLUSIVE_INSTALL_HASHES_PASS',request_sha256=QH,archive_sha256=AH,targets=list(expected.values()),read_manifest=ROWS,verification_seconds=time.monotonic()-START,real_data_reads=0,checkpoint_reads=0,arrays_decoded=0,checkpoint_deserialization=0,overwritten_files=0,identity=I,GPU_query=gpu))
 phase('materialize_one_way_authorization_runtime_launcher')
 auth=dict(schema='bcsp-lqi-cuda-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='User: 已上传，单独授权此request完整SHA256，才能不覆盖安装并执行唯一一次准入。 References '+QH+'; exclusive8-file installation; ONE LQI artificial CUDA admission, exact2F2loss2B0optimizer; stop first failure, no retry/resume, no real payload/checkpoint/BNCal/training run.')
 emit(L['authorization_path'],auth);asha=sha(L['authorization_path'])
 emit(L['runtime_path'],dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256=QH,authorization_sha256=asha));rsha=sha(L['runtime_path'])
 def record(path):p=clean(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
 namespace['authorize'](q,QH,auth,asha,dict(schema='bcsp-lqi-cuda-runtime-v1',request_sha256=QH,authorization_sha256=asha))
 # P3 and final entry/adapter bindings are checked by actual authorize above.
 launcher=namespace['render_launcher'](q,QH,asha,rsha)
 with clean(L['launcher_path']).open('xb') as f:f.write(launcher.encode('utf-8'));f.flush();os.fsync(f.fileno())
 os.chmod(L['launcher_path'],0o700);subprocess.run(['/bin/bash','-n',L['launcher_path']],check=True,timeout=5)
 need(not out.exists() and time.monotonic()-START<=120,'last output/time gate');smi(I);absent_session(L['tmux_session'])
 emit(L['launch_attempt_path'],dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH))
 phase('single_attempt_claimed_before_tmux')
 result=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'-c',str(PROJECT),'/bin/bash '+shlex.quote(L['launcher_path'])],capture_output=True,timeout=10)
 need(result.returncode==0,'tmux failed: '+repr(result.stderr[:512]));time.sleep(2)
 live=subprocess.run(['tmux','has-session','-t',L['tmux_session']],capture_output=True,timeout=5).returncode==0
 receipt=dict(status='AUTHORIZED_SINGLE_LAUNCH_RETURNED_INSPECT_STARTUP',request_sha256=QH,tmux_returncode=result.returncode,session=L['tmux_session'],session_present=live,authorization_sha256=asha,runtime_sha256=rsha,launcher_sha256=sha(L['launcher_path']),output=str(out),exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,log_tail=Path(L['log']).read_text(errors='replace')[-5000:] if Path(L['log']).exists() else None)
 emit(control/'startup_receipt_v1.json',receipt);print(json.dumps(receipt),flush=True)

# Exact sidecar bindings are inserted locally before this one-shot operation is transported.
SIDECARS=[{'path': '/home/jovyan/bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.sha256', 'bytes': 119, 'sha256': '7ee3693a1e422d7c98d78567da3c806a677b38fdc84119e3a95c3cab4750f6c3'}, {'path': '/home/jovyan/bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.bytes', 'bytes': 7, 'sha256': 'd1e24ae996d4fb4dbdd42f40ac1105cf60ddd4320df043fe0b731d6276af0a84'}, {'path': '/home/jovyan/bcsp_lqi_artificial_cuda_pending_20261111_v1.tar.gz.contents.sha256', 'bytes': 924, 'sha256': 'efa5493c4566f3773e2e206258844e0936627896c838f49de167149a61a44e83'}]
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  failure=dict(status='AUTHORIZED_OPERATION_FAILED_STOP_NO_RETRY',phase=PHASE,error=repr(exc),hashed_bytes=READ,seconds=time.monotonic()-START,installation_root_exists=INSTALL.exists())
  control=INSTALL/'control'
  if control.is_dir() and not (control/'operation_failure_v1.json').exists():emit(control/'operation_failure_v1.json',failure)
  print(json.dumps(failure),flush=True);raise
