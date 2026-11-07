"""One frozen authorized verify/install/materialize/launch operation, no retry."""
import hashlib,json,os,shlex,shutil,socket,subprocess,tarfile,time,sys
from pathlib import Path
QH='9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c'
AH='934b6a011029a976f5c4c8ae868d8c7f07048e5209496387837ee5eb5535acf3'
ARCHIVE=Path('/home/jovyan/bcsp_p2_condition_probe_pending_20261107_v1.tar.gz')
INSTALL=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1')
START=time.monotonic();PHASE='start';READ=0;ROWS=[]
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def clean(path):
 p=Path(path);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/path: '+str(p));return p
def exact(r):
 global READ
 p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'],'missing/type/size: '+str(p));before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   READ+=len(b);need(READ<=6*1024**3 and time.monotonic()-START<=150,'verification read/time budget');h.update(b)
 after=p.stat();need((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'read drift: '+str(p));need(h.hexdigest()==r['sha256'],'hash: '+str(p));ROWS.append(r);return p
def sha(p):return hashlib.sha256(clean(p).read_bytes()).hexdigest()
def emit(p,obj):
 with clean(p).open('x',encoding='ascii') as f:json.dump(obj,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())
def stage(s):
 global PHASE
 PHASE=s;print(json.dumps(dict(phase=s,seconds=time.monotonic()-START,hashed_bytes=READ)),flush=True)
def smi(I):
 v=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().split(',');need([x.strip() for x in v[:4]]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
def main():
 stage('uploaded_archive_and_frozen_request')
 need(socket.gethostname()=='shu-common-25721452-notebook-1lvq9b-0' and os.getuid()==1000,'identity')
 exact(dict(path=str(ARCHIVE),bytes=217631,sha256=AH))
 need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0]==AH and int(Path(str(ARCHIVE)+'.bytes').read_text())==217631,'archive sidecars')
 payload={}
 with tarfile.open(ARCHIVE,'r:gz') as t:
  members=t.getmembers();need(len(members)==6,'exact six archive members')
  for m in members:
   need(m.isfile() and m.name==Path(m.name).name and m.name not in payload and m.size<=2*1024**2,'member boundary');payload[m.name]=t.extractfile(m).read()
 need(hashlib.sha256(payload['condition_probe_execution_request_v1.json']).hexdigest()==QH,'authorized request hash')
 q=json.loads(payload['condition_probe_execution_request_v1.json']);I=q['identity'];L=q['launch_contract'];out=clean(q['output']);need(q['prefix_budget']==1680 and all(q[k]==0 for k in ['backward','optimizer_steps','dense_forwards','BNCal']),'contract')
 expected={Path(q[k]['path']).name:q[k] for k in ['entry','capture','core','input_index','P3']};expected['condition_probe_execution_request_v1.json']=dict(path=str(INSTALL/'condition_probe_execution_request_v1.json'),bytes=len(payload['condition_probe_execution_request_v1.json']),sha256=QH)
 need(set(payload)==set(expected),'archive exact targets')
 for name,b in expected.items():need(len(payload[name])==b['bytes'] and hashlib.sha256(payload[name]).hexdigest()==b['sha256'] and clean(b['path']).parent==INSTALL,'member hash/mapping '+name)
 listing=''.join(hashlib.sha256(payload[n]).hexdigest()+'  '+n+'\n' for n in payload);need(Path(str(ARCHIVE)+'.contents.sha256').read_text()==listing,'contents sidecar')
 need(not clean(INSTALL).exists() and not out.exists(),'new install/output absent')
 need(INSTALL.parent.is_dir() and clean(I['project']).is_dir(),'existing safe parents')
 need(subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1,'tmux absent')
 smi(I);need(shutil.disk_usage(I['project']).free>=q['limits']['minimum_free_disk_bytes'],'disk')
 stage('exact_reused_sources_and_dependencies')
 for r in [q['parent_entry'],q['helper'],q['preflight_scope'],q['static_config'],q['numeric_policy'],*q['implementation'].values(),*q['dependencies']]:exact(r)
 scope=json.loads(Path(q['preflight_scope']['path']).read_bytes());bindings=scope['bindings'];modelroot=clean(q['model_root'])
 for r in bindings['candidate']:exact(dict(path=str(modelroot/r['relative_target']),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['isolated_model_project_sources']:exact(dict(path=str(modelroot/r['relative_path']),bytes=r['bytes'],sha256=r['sha256']))
 for r in bindings['provider']+bindings['environment_metadata']:exact(r)
 c=bindings['base_config'];need(sha(modelroot/'base_model.yaml')==c['sha256'],'base yaml')
 version=subprocess.check_output([I['python_realpath'],'-I','-S','-B','-c','import sys;print(sys.version.split()[0])'],timeout=10,text=True).strip();need(version==I['python_version'],'Python version')
 stage('four_checkpoint_and_exact_role_point_files')
 idx=json.loads(payload['condition_probe_input_index_v1.json']);need(len(idx['runs'])==4 and len(idx['inputs'])==1680,'fixed index')
 for run in idx['runs']:exact(run['checkpoint'])
 unique={}
 for r in idx['inputs']:
  b=r['input'];need(b['path'].startswith('/home/jovyan/adapointr_work/PoinTr/data/') and Path(b['path']).name==r['case_id']+'_8192.npz','point scope')
  if b['path'] in unique:need(unique[b['path']]==b,'conflicting bindings')
  unique[b['path']]=b
 for b in unique.values():exact(b)
 stage('all_readiness_pass_before_exclusive_install')
 need(not clean(INSTALL).exists() and not out.exists(),'targets drift');smi(I)
 INSTALL.mkdir()
 for name,blob in payload.items():
  with (INSTALL/name).open('xb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
  exact(expected[name])
 control=INSTALL/'control';control.mkdir();receipt=control/'readiness_and_installation_receipt_v1.json';emit(receipt,dict(status='EXCLUSIVE_INSTALL_HASHES_PASS',request_sha256=QH,files=[expected[n] for n in payload],exact_unique_point_paths=len(unique),unique_cases=len({r['case_id'] for r in idx['inputs']}),read_manifest=ROWS,verification_seconds=time.monotonic()-START))
 stage('one_way_authorization_runtime_launcher')
 auth=dict(schema='bcsp-condition-probe-authorization-v1',request_sha256=QH,explicit_user_authorization=True,user_authorization_text='User uploaded the package and separately authorized execution of complete SHA256 '+QH+' in this conversation on 2026-11-07; no training or automatic retry.')
 emit(L['authorization_path'],auth);authsha=sha(L['authorization_path']);emit(L['runtime_path'],dict(schema='bcsp-condition-probe-runtime-v1',request_sha256=QH,authorization_sha256=authsha));runtime_sha=sha(L['runtime_path'])
 command=['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s',I['python_realpath'],'-I','-S','-B',q['entry']['path'],'--request',L['request_path'],'--request-sha256',QH,'--authorization',L['authorization_path'],'--authorization-sha256',authsha,'--runtime',L['runtime_path'],'--runtime-sha256',runtime_sha]
 env=[k+'='+v.replace('<owned_output>',str(out)) for k,v in q['environment'].items()]
 launch='#!/bin/bash\nset -u\numask 077\ncd '+shlex.quote(I['project'])+' || exit 120\n'
 for p in [*reversed(out.parents),out]:
  if str(p)!='/':launch+='[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n'
 launch+='mkdir -p -- '+shlex.quote(str(out.parent))+' || exit 122\nmkdir -- '+shlex.quote(str(out))+' || exit 123\nexec >>'+shlex.quote(L['log'])+' 2>&1\nenv \\\n'
 launch+=' \\\n'.join(shlex.quote(x) for x in env+command)+'\nresult=$?\nprintf "%s\\n" "$result" > '+shlex.quote(L['exit_code'])+'\nexit "$result"\n'
 need(max(map(len,launch.splitlines()))<=2048,'launcher line budget')
 with clean(L['launcher_path']).open('x',encoding='ascii') as f:f.write(launch);f.flush();os.fsync(f.fileno())
 os.chmod(L['launcher_path'],0o700)
 subprocess.run(['/bin/bash','-n',L['launcher_path']],check=True,timeout=5)
 need(not out.exists() and subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1,'last single-use gate');smi(I)
 emit(q['launch_attempt'],dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH));stage('single_attempt_claimed')
 r=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'-c',I['project'],'/bin/bash '+shlex.quote(L['launcher_path'])],capture_output=True,text=True,timeout=10);need(r.returncode==0,'tmux start '+r.stderr[:512]);time.sleep(2)
 live=subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
 status=dict(status='AUTHORIZED_SINGLE_LAUNCH_RETURNED',request_sha256=QH,tmux_returncode=r.returncode,session=L['tmux_session'],session_present=live,authorization_sha256=authsha,runtime_sha256=runtime_sha,launcher_sha256=sha(L['launcher_path']),output=str(out),exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,log_tail=Path(L['log']).read_text(errors='replace')[-4500:] if Path(L['log']).exists() else None)
 emit(control/'startup_receipt_v1.json',status);print(json.dumps(status),flush=True)
try:main()
except BaseException as exc:
 print(json.dumps(dict(status='AUTHORIZED_OPERATION_FAILED_STOP_NO_RETRY',phase=PHASE,error=repr(exc),hashed_bytes=READ,seconds=time.monotonic()-START,installation_root_exists=INSTALL.exists())),flush=True);raise
