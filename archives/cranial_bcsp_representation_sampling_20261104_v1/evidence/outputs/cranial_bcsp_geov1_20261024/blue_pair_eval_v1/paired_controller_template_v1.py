"""Frozen evaluation-specific install/launch template. Importing never executes it."""
import hashlib,io,json,os,shlex,shutil,socket,stat,subprocess,tarfile,time
from pathlib import Path
FROZEN_DATA_DIRECTORIES=['/home/jovyan/adapointr_work/PoinTr/data/bcsp_blue_pair_dev_v1', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_blue_pair_dev_v1/Euclidean_elimination', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_blue_pair_dev_v1/Euclidean_elimination/points', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_blue_pair_dev_v1/surface_graph', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_blue_pair_dev_v1/surface_graph/points']

def need(ok,text):
 if not ok:raise RuntimeError(text)
def h(raw):return hashlib.sha256(raw).hexdigest()
def raw_json(obj):return (json.dumps(obj,ensure_ascii=True,indent=2,allow_nan=False)+'\n').encode()
def safe(p):
 p=Path(p).absolute();need(not any(x.is_symlink() for x in (p,*p.parents)),'link: '+str(p));return p
def file_hash(p):
 result=hashlib.sha256()
 with safe(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):result.update(block)
 return result.hexdigest()
def exact(r):
 p=safe(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'] and file_hash(p)==r['sha256'],'bound file: '+str(p));return p
def create(p,data):
 p=safe(p);need(p.parent.is_dir(),'parent missing: '+str(p.parent))
 fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 need(p.read_bytes()==data,'exclusive write readback');return dict(path=str(p),bytes=len(data),sha256=h(data))
def materials(q,entry_raw,grant):
 need(bool(grant.strip()),'explicit grant text')
 control=Path(q['control']);digest=h(entry_raw)
 auth=raw_json(dict(schema='bcsp-development-authorization-v1',request_sha256=digest,explicit_user_authorization=True,user_authorization_text=grant))
 runtime=raw_json(dict(schema='bcsp-development-runtime-v1',request_sha256=digest,authorization_sha256=h(auth)))
 paths=[control/x for x in ['entry_request.json','authorization.json','runtime.json']]
 lines=['#!/usr/bin/env bash','set -u','set -o pipefail','set -o noclobber','umask 077','cd /home/jovyan/adapointr_work/PoinTr || exit 65']
 for key,value in q['environment'].items():lines.append('export '+key+'='+shlex.quote(value.replace('<owned_output>',q['output'])))
 for p,b in zip(paths,[entry_raw,auth,runtime]):
  lines.append('[ "$(sha256sum -- '+shlex.quote(str(p))+" | cut -d ' ' -f 1)\" = "+h(b)+' ] || exit 65')
 lines+=['[ -d '+shlex.quote(q['output'])+' ] && [ ! -L '+shlex.quote(q['output'])+' ] || exit 73','set +e']
 cmd=['/usr/bin/timeout','--signal=TERM','--kill-after=5s',str(q['limits']['wall_seconds'])+'s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path']]
 for key,path,b in zip(['request','authorization','runtime'],paths,[entry_raw,auth,runtime]):cmd+=['--'+key,str(path),'--'+key+'-sha256',h(b)]
 lines.append(' '.join(shlex.quote(x) for x in cmd)+' > '+shlex.quote(q['output']+'/launch.log')+' 2>&1')
 lines+=['eval_rc=$?','printf \'%s\\n\' "$eval_rc" > '+shlex.quote(q['output']+'/exit_code.txt'),'save_rc=$?','[ "$save_rc" -eq 0 ] || exit 74','exit "$eval_rc"']
 return dict(authorization=auth,runtime=runtime,launcher=('\n'.join(lines)+'\n').encode())
def archive_members(blob,mapping):
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as tar:
  files=tar.getmembers();need(len(files)==len(mapping)==213 and len({r['member'] for r in mapping})==213 and len({r['target'] for r in mapping})==213 and {m.name for m in files}=={r['member'] for r in mapping},'exact two-file transport')
  result={}
  for r in mapping:
   m=tar.getmember(r['member']);need(m.isfile() and m.size==r['bytes'] and 0<m.size<=1048576,'transport member type/size')
   data=tar.extractfile(m).read();need(h(data)==r['sha256'],'transport member hash');result[r['target']]=data
  return result
def run(scope_raw,scope_sha,entry_raw,grant):
 need(h(scope_raw)==scope_sha,'frozen outer request hash');scope=json.loads(scope_raw)
 need(scope['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and scope['execution_authorized'] is False and bool(grant.strip()),'separate full-SHA grant required')
 need(h(entry_raw)==scope['entry_request']['sha256'] and len(entry_raw)==scope['entry_request']['bytes'],'inner request bytes')
 q=json.loads(entry_raw);i=q['identity'];created=[];attempted=False;phase='precheck';start=time.monotonic()
 try:
  need(socket.gethostname()==i['hostname'] and os.getuid()==i['uid'],'container identity');os.chdir('/home/jovyan/adapointr_work/PoinTr')
  exact(scope['upload']);mapping=scope['install_mapping'];content=archive_members(Path(scope['upload']['path']).read_bytes(),mapping)
  for r in scope['upload_sidecars']:exact(r)
  directories=scope['new_data_directories'];need(directories==FROZEN_DATA_DIRECTORIES,'exact new directories')
  for d in directories:need(not os.path.lexists(str(safe(d))),'data directory exists: '+d)
  need(safe(directories[0]).parent.is_dir(),'new data parent missing')
  for target in [r['target'] for r in mapping]+[q['control'],q['output']]:
   p=safe(target);need(not os.path.lexists(str(p)) and (p.parent.is_dir() or str(p.parent) in directories),'target occupied/parent missing: '+target)
  for r in scope['reused_assets']:exact(r)
  need(shutil.disk_usage('/home/jovyan/adapointr_work/PoinTr').free>=q['limits']['minimum_free_disk_bytes'],'free disk')
  command=['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']
  fields=[x.strip() for x in subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip().split(',')]
  need(fields[:4]==[i['gpu_uuid'],i['gpu_name'],i['driver_version'],str(i['nvidia_smi_memory_total_MiB'])] and int(fields[4])<=256,'GPU identity/idle')
  pids=subprocess.run(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip();need(not pids,'initial GPU process')
  test=subprocess.run(['/usr/bin/tmux','has-session','-t',scope['tmux_session']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10);need(test.returncode==1,'tmux session exists/unavailable')
  need(time.monotonic()-start<=90,'pre-launch controller budget')
  phase='exclusive_install'
  for d in directories:safe(d).mkdir(mode=0o700)
  for r in mapping:created.append(create(r['target'],content[r['target']]))
  phase='materialize_single_attempt';control=safe(q['control']);control.mkdir(mode=0o700);output=safe(q['output']);output.mkdir(mode=0o700)
  m=materials(q,entry_raw,grant)
  for name,data in [('execution_scope.json',scope_raw),('entry_request.json',entry_raw),('authorization.json',m['authorization']),('runtime.json',m['runtime']),('evaluate_once.sh',m['launcher']),('launch_attempt.json',raw_json(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=h(entry_raw))))]:created.append(create(control/name,data))
  need(str(control/'launch_attempt.json')==q['launch_attempt'],'claim path binding')
  print(json.dumps(dict(status='EVALUATION_MATERIALIZED_ATTEMPT_CLAIMED',files=created,scope_sha256=scope_sha)),flush=True)
  phase='tmux_start';attempted=True
  result=subprocess.run(['/usr/bin/tmux','new-session','-d','-s',scope['tmux_session'],'/bin/bash '+shlex.quote(str(control/'evaluate_once.sh'))],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
  need(result.returncode==0,'tmux start returncode '+str(result.returncode));time.sleep(1)
  alive=subprocess.run(['/usr/bin/tmux','has-session','-t',scope['tmux_session']],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10).returncode==0
  exitfile=output/'exit_code.txt';code=exitfile.read_text().strip() if exitfile.is_file() else None
  print(json.dumps(dict(status='EVALUATION_START_OBSERVED',session=scope['tmux_session'],session_alive=alive,exit_code=code,output=str(output),launch_log=str(output/'launch.log'),no_retries=True)),flush=True)
  need(alive or code=='0','session absent and no successful exit')
 except BaseException as exc:
  print(json.dumps(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),tmux_attempted=attempted,created_files=created)),flush=True);raise
