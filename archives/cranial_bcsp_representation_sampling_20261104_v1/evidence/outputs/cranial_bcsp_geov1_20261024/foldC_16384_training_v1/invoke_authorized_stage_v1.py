from pathlib import Path
import base64,hashlib,json,subprocess,sys,datetime
A=Path(__file__).resolve().parent/'authorized_execution_v1'
stage=sys.argv[1];assert stage in ['install','training']
if stage=='training':
 cap=json.loads((A/'install_process_capture_v1.json').read_bytes());assert cap['returncode']==0
 ev=json.loads((A/'install_server_events_v1.json').read_bytes())
 assert any(x.get('status')=='DATA316_INSTALLATION_HASH_PASS' for x in ev)
driver=(A/('invoke_'+stage+'_once_v1.py')).read_bytes()
payload=(A/('install_data316_once_v1.py' if stage=='install' else 'materialize_and_start_once_v1.py')).read_bytes()
data=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode()
command="import base64;exec(compile(base64.b64decode("+repr(base64.b64encode(driver).decode())+"),'<authorized_short_driver>','exec'))"
with (A/(stage+'_attempt_started_v1.json')).open('x') as f:json.dump(dict(UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),payload_sha256=hashlib.sha256(payload).hexdigest(),driver_sha256=hashlib.sha256(driver).hexdigest()),f)
try:
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=r.returncode,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode(),timeout=False)
except subprocess.TimeoutExpired as e:
 cap=dict(returncode=None,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),timeout=True)
with (A/(stage+'_process_capture_v1.json')).open('x') as f:json.dump(cap,f,indent=2)
events=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:d=json.loads(line)
 except ValueError:continue
 if isinstance(d,dict):events.append(d)
with (A/(stage+'_server_events_v1.json')).open('x') as f:json.dump(events,f,indent=2)
print(json.dumps(dict(stage=stage,returncode=cap['returncode'],timeout=cap['timeout'],events=[{k:v for k,v in e.items() if k not in ['auth_content_base64','runtime_content_base64','launcher_content_base64','files','paths']} for e in events])))
raise SystemExit(0 if cap['returncode']==0 else 1)
