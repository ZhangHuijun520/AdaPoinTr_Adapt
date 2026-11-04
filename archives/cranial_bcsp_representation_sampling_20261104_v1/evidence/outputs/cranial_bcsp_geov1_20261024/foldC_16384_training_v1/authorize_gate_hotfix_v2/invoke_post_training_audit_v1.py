from pathlib import Path
import ast,base64,hashlib,json,subprocess
N=Path(__file__).resolve().parent
A=N/'freeze_audit_v1';A.mkdir(exist_ok=False)
events=json.loads((N/'authorized_execution_v1/training_server_events_v1.json').read_bytes())
expected=next(x['files'] for x in events if x.get('status')=='TRAIN_MATERIALIZED_AND_ATTEMPT_CLAIMED')
source='EXPECTED_CONTROL='+repr(expected)+'\n'+(N/'post_training_audit_v1.py').read_text()
compile(source,'fixed_post_training_readonly_audit','exec')
payload=source.encode()
with (A/'frozen_audit_payload_v1.py').open('xb') as f:f.write(payload)
base=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
t=base/'outputs/cranial_bcsp_geov1_20261024/resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=t.read_bytes()
assert hashlib.sha256(driver).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
driver=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
with (A/'invoke_short_readonly_v1.py').open('xb') as f:f.write(driver)
scope=dict(status='AUTHORIZED_READONLY_POST_TRAINING_AUDIT',expected_hostname='shu-common-25721452-notebook-01dt08-0',
 maximum_output_entries=32,maximum_read_bytes=536870912,checkpoint_max_bytes=402653184,ordinary_file_max_bytes=16777216,
 audit_budget_seconds=90,external_timeout_seconds=120,client_timeout_seconds=135,local_timeout_seconds=155,
 payload_sha256=hashlib.sha256(payload).hexdigest(),server_writes=0,checkpoint_deserialization=False,CUDA_calls=0,retries=0)
with (A/'frozen_scope_v1.json').open('x') as f:json.dump(scope,f,indent=2)
with (A/'attempt_started_v1.json').open('x') as f:json.dump(dict(scope_sha256=hashlib.sha256((A/'frozen_scope_v1.json').read_bytes()).hexdigest()),f)
data=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode()
command='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<readonly_audit_driver>","exec"))'
try:
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=r.returncode,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode(),timeout=False)
except subprocess.TimeoutExpired as e:
 cap=dict(returncode=None,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),timeout=True)
with (A/'process_capture_v1.json').open('x') as f:json.dump(cap,f,indent=2)
items=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:d=json.loads(line)
 except ValueError:continue
 if isinstance(d,dict):items.append(d)
with (A/'server_events_v1.json').open('x') as f:json.dump(items,f,indent=2)
report=next((x for x in reversed(items) if x.get('status') in ['FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS','AUDIT_FAILED_STOP_NO_RETRY']),None)
if report:
 with (A/'audit_report_v1.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['all_bound_files','output_manifest']}))
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],report_received=report is not None)))
raise SystemExit(0 if cap['returncode']==0 and report and report['status']=='FORMAL_POST_TRAINING_FREEZE_AUDIT_PASS' else 1)
