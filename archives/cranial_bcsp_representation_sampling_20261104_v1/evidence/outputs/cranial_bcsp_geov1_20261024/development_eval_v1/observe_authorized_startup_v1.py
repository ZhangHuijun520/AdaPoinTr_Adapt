"""One bounded read-only startup observation; not a formal post-evaluation audit."""
from pathlib import Path
import base64,hashlib,json,subprocess
N=Path(__file__).resolve().parent;A=N/'authorized_execution_v1';O=A/'completion_observation_v1';O.mkdir(exist_ok=False)
q=json.loads((N/'development_entry_request_v1.json').read_bytes());session='bcsp_dev_four_models_seed0_v1'
payload=('OUT='+repr(q['output'])+'\nHOST='+repr(q['identity']['hostname'])+'\nSESSION='+repr(session)+'''\nimport json,os,socket,subprocess
from pathlib import Path
assert socket.gethostname()==HOST and os.getuid()==1000,'container identity'
out=Path(OUT);assert out.is_dir() and not any(p.is_symlink() for p in (out,*out.parents)),'output path'
def read(name):
 p=out/name
 if not p.exists():return None
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576,'text budget '+name
 return p.read_text()
code=read('exit_code.txt');failure=read('failure.json');completed=read('inference_complete.json');completion=read('completion.json')
p=out/'inference_manifest.jsonl';count=0;last=None
if p.exists():
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=1048576,'inference manifest budget'
 rows=p.read_text().splitlines();count=len(rows)
 if rows:last=json.loads(rows[-1])
resources=None;p=out/'resources.jsonl'
if p.exists():
 assert p.is_file() and not p.is_symlink() and p.stat().st_size<=4194304,'resource log budget'
 lines=p.read_text().splitlines()
 if lines:resources=json.loads(lines[-1])
tail='';p=out/'launch.log'
if p.exists():
 assert not p.is_symlink() and p.stat().st_size<=1048576,'launch log budget'
 tail='\\n'.join(p.read_text(errors='replace').splitlines()[-18:])
alive=subprocess.run(['/usr/bin/tmux','has-session','-t',SESSION],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode==0
print(json.dumps(dict(status='READONLY_STARTUP_OBSERVATION',hostname=socket.gethostname(),session_alive=alive,exit_code=code.strip() if code else None,prediction_records=count,last_prediction=last,last_resources=resources,failure=json.loads(failure) if failure else None,inference_complete=json.loads(completed) if completed else None,completion=json.loads(completion) if completion else None,launch_log_tail=tail,server_writes=0,forward_calls_from_observer=0,formal_freeze_audit=False)))
''').encode()
compile(payload,'readonly_startup_observation','exec')
with (O/'payload.py').open('xb') as f:f.write(payload)
t=N.parent/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=t.read_bytes();assert hashlib.sha256(driver).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
driver=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
with (O/'short_driver.py').open('xb') as f:f.write(driver)
with (O/'attempt.json').open('x') as f:json.dump(dict(payload_sha256=hashlib.sha256(payload).hexdigest(),server_writes=0),f)
cmd='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<readonly_startup_observation>","exec"))'
try:
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',cmd],input=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=r.returncode,timeout=False,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode())
except subprocess.TimeoutExpired as e:cap=dict(returncode=None,timeout=True,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode())
with (O/'capture.json').open('x') as f:json.dump(cap,f,indent=2)
events=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:x=json.loads(line)
 except ValueError:continue
 if isinstance(x,dict):events.append(x)
report=next((x for x in reversed(events) if x.get('status')=='READONLY_STARTUP_OBSERVATION'),None)
if report:
 with (O/'report.json').open('x') as f:json.dump(report,f,indent=2)
 preview={k:report[k] for k in ['status','hostname','session_alive','exit_code','prediction_records','failure','inference_complete','formal_freeze_audit']}
 preview['last_resources']=report['last_resources']
 if report['completion']:
  done=report['completion'];preview['completion']={k:v for k,v in done.items() if k!='archive'}
  preview['completion']['archive']={k:v for k,v in done['archive'].items() if k!='members'}
 print(json.dumps(preview))
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],report_received=report is not None)))
raise SystemExit(0 if cap['returncode']==0 and report else 1)
