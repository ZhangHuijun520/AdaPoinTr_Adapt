"""Execute one newly authorized bounded read-only post-prediction audit."""
from pathlib import Path
import base64,hashlib,json,subprocess
N=Path(__file__).resolve().parent
outer_sha='85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea'
qraw=(N/'development_execution_request_v1.json').read_bytes();assert hashlib.sha256(qraw).hexdigest()==outer_sha
outer=json.loads(qraw);inner_path=Path(outer['entry_request']['path']);inner_raw=inner_path.read_bytes()
assert hashlib.sha256(inner_raw).hexdigest()==outer['entry_request']['sha256'];q=json.loads(inner_raw)
events=json.loads((N/'authorized_execution_v1/server_events.json').read_bytes())
controls=next(x['files'] for x in events if x.get('status')=='EVALUATION_MATERIALIZED_ATTEMPT_CLAIMED')
observed=json.loads((N/'authorized_execution_v1/completion_observation_v1/report.json').read_bytes())['completion']['archive']
A=N/'freeze_audit_v1';A.mkdir(exist_ok=False)
scope=dict(schema='bcsp-four-model-readonly-post-prediction-audit-v1',outer_sha256=outer_sha,inner_sha256=outer['entry_request']['sha256'],
 identity=q['identity'],output=q['output'],control=q['control'],session=outer['tmux_session'],controls=controls,
 observed_archive={k:observed[k] for k in ['path','bytes','sha256']},limits=dict(read_bytes=2147483648,wall_seconds=90),
 read_scope='Exact8 installation/control files;4 checkpoint hashes;fixed fold binding;13 result entries and420 predictions;423-member archive;4 download artifacts',
 server_writes=0,model_imports=0,checkpoint_deserialization=False,CUDA_calls=0,forward_calls=0)
with (A/'scope.json').open('x') as f:json.dump(scope,f,indent=2)
code=(N/'post_prediction_freeze_audit_v1.py').read_bytes()
prefix=b'import base64,json\nSPEC=json.loads(base64.b64decode('+repr(base64.b64encode(json.dumps(scope).encode()).decode()).encode()+b'))\n'
payload=prefix+code;compile(payload,'formal_readonly_post_prediction_audit','exec')
with (A/'frozen_payload.py').open('xb') as f:f.write(payload)
template=N.parent/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=template.read_bytes();assert hashlib.sha256(driver).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
driver=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
with (A/'short_driver.py').open('xb') as f:f.write(driver)
with (A/'attempt_started.json').open('x') as f:json.dump(dict(scope_sha256=hashlib.sha256((A/'scope.json').read_bytes()).hexdigest(),payload_sha256=hashlib.sha256(payload).hexdigest(),audit_source_sha256=hashlib.sha256(code).hexdigest(),server_writes=0,retries=0),f,indent=2)
command='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<formal_post_prediction_audit>","exec"))'
try:
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=r.returncode,timeout=False,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode())
except subprocess.TimeoutExpired as e:cap=dict(returncode=None,timeout=True,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode())
with (A/'process_capture.json').open('x') as f:json.dump(cap,f,indent=2)
items=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:item=json.loads(line)
 except ValueError:continue
 if isinstance(item,dict):items.append(item)
with (A/'server_events.json').open('x') as f:json.dump(items,f,indent=2)
report=next((x for x in reversed(items) if x.get('status') in ['FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS','FORMAL_POST_PREDICTION_FREEZE_AUDIT_FAILED_STOP']),None)
if report:
 with (A/'audit_report.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps({k:v for k,v in report.items() if k not in ['prediction_manifest','control_hashes','state_evidence','checkpoint_hashes']}))
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],report_received=report is not None)))
raise SystemExit(0 if cap['returncode']==0 and report and report['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS' else 1)
