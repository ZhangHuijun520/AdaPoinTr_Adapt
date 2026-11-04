from pathlib import Path
import base64,hashlib,json,subprocess
N=Path(__file__).resolve().parent
payload=(N/'server_readiness_payload_v1.py').read_bytes();driver=(N/'server_readiness_short_driver_v2.py').read_bytes()
with (N/'server_readiness_attempt_v2.json').open('x') as f:json.dump(dict(scope_sha256=hashlib.sha256((N/'server_readiness_scope_v1.json').read_bytes()).hexdigest(),payload_sha256=hashlib.sha256(payload).hexdigest(),server_writes=0),f)
command='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<finite_readiness>","exec"))'
try:
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=r.returncode,timeout=False,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode())
except subprocess.TimeoutExpired as e:cap=dict(returncode=None,timeout=True,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode())
with (N/'server_readiness_capture_v2.json').open('x') as f:json.dump(cap,f,indent=2)
items=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:item=json.loads(line)
 except ValueError:continue
 if isinstance(item,dict):items.append(item)
report=next((x for x in reversed(items) if x.get('status') in ['FOUR_MODEL_DEVELOPMENT_READINESS_PASS','READINESS_FAILED_STOP']),None)
with (N/'server_readiness_events_v2.json').open('x') as f:json.dump(items,f,indent=2)
if report:
 with (N/'server_readiness_report_v2.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k!='files'}))
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],report_received=report is not None)))
raise SystemExit(0 if cap['returncode']==0 and report and report['status']=='FOUR_MODEL_DEVELOPMENT_READINESS_PASS' else 1)
