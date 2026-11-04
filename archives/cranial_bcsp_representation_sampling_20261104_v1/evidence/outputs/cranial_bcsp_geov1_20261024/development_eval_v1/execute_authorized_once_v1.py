"""Current explicit user grant: frozen two-file install and one420-forward launch."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess

N=Path(__file__).resolve().parent
SHA='85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea'
scope_raw=(N/'development_execution_request_v1.json').read_bytes()
assert hashlib.sha256(scope_raw).hexdigest()==SHA
scope=json.loads(scope_raw)
assert scope['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and scope['execution_authorized'] is False
def read_bound(r):
 p=Path(r['path']);raw=p.read_bytes()
 assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
 return raw
entry_raw=read_bound(scope['entry_request']);controller_raw=read_bound(scope['controller_template'])
read_bound(scope['local_upload']);read_bound(scope['local_P3']);read_bound(scope['reference_manifest'])
A=N/'authorized_execution_v1';A.mkdir(exist_ok=False)
user_text='下一步单独授权以下request完整SHA256，才能限定安装并启动唯一一次四模型、420次预测'
grant=dict(schema='bcsp-human-contextual-execution-grant-v1',request_sha256=SHA,explicit_user_authorization=True,
 user_message_verbatim=user_text,reference_resolution='The current human turn refers to the immediately preceding displayed full request SHA256;no replacement request.',
 granted_scope='Frozen exclusive two-file install and unique420-forward four-model prediction;no training/BNCal/scoring/retry',
 recorded_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (A/'explicit_grant.json').open('x',encoding='utf-8') as f:json.dump(grant,f,ensure_ascii=False,indent=2)
grant_text=user_text+'\n上下文绑定的request完整SHA256：'+SHA
# Preserve all frozen files as original bytes: never reserialize request/controller.
tail='\nimport base64\nrun(base64.b64decode('+repr(base64.b64encode(scope_raw).decode())+'),'+repr(SHA)+',base64.b64decode('+repr(base64.b64encode(entry_raw).decode())+'),base64.b64decode('+repr(base64.b64encode(grant_text.encode('utf-8')).decode())+').decode("utf-8"))\n'
payload=controller_raw+b'\n'+tail.encode('ascii')
compile(payload,'authorized_frozen_evaluation_controller','exec')
with (A/'materialize_and_start_once.py').open('xb') as f:f.write(payload)
template=N.parent/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=template.read_bytes()
assert hashlib.sha256(driver).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
driver=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
with (A/'invoke_short_once.py').open('xb') as f:f.write(driver)
with (A/'attempt_started.json').open('x') as f:json.dump(dict(request_sha256=SHA,grant_sha256=hashlib.sha256((A/'explicit_grant.json').read_bytes()).hexdigest(),payload_sha256=hashlib.sha256(payload).hexdigest(),retries=0),f,indent=2)
command='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<authorized_eval_once>","exec"))'
try:
 result=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=result.returncode,timeout=False,stdout_base64=base64.b64encode(result.stdout).decode(),stderr_base64=base64.b64encode(result.stderr).decode())
except subprocess.TimeoutExpired as e:
 cap=dict(returncode=None,timeout=True,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode())
with (A/'process_capture.json').open('x') as f:json.dump(cap,f,indent=2)
events=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:event=json.loads(line)
 except ValueError:continue
 if isinstance(event,dict):events.append(event)
with (A/'server_events.json').open('x') as f:json.dump(events,f,indent=2)
started=next((x for x in reversed(events) if x.get('status')=='EVALUATION_START_OBSERVED'),None)
failure=next((x for x in reversed(events) if x.get('status')=='FAILED_STOP_NO_RETRY'),None)
summary=dict(status='SINGLE_ATTEMPT_START_OBSERVED' if cap['returncode']==0 and started and not failure else 'STOPPED_NO_RETRY',request_sha256=SHA,returncode=cap['returncode'],timeout=cap['timeout'],start_observation=started,failure=failure,training=0,BNCal=0,CPU_scoring=0,retries=0)
with (A/'execution_result.json').open('x') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary))
raise SystemExit(0 if summary['status']=='SINGLE_ATTEMPT_START_OBSERVED' else 1)
