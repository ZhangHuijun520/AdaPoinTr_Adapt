"""Read-only upload check; no deployment or execution authorization materialization."""
from pathlib import Path
import base64,hashlib,json,subprocess
N=Path(__file__).resolve().parent
Q=N/'development_execution_request_v1.json'
expected='85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea'
assert hashlib.sha256(Q.read_bytes()).hexdigest()==expected
q=json.loads(Q.read_bytes());inner=json.loads(Path(q['entry_request']['path']).read_bytes())
A=N/'upload_verification_v1';A.mkdir(exist_ok=False)
spec=dict(request_sha256=expected,identity=inner['identity'],upload=q['upload'],members=q['install_mapping'],
 targets=[r['target'] for r in q['install_mapping']]+[inner['control'],inner['output']],
 limits=dict(wall_seconds=30,archive_bytes=1048576,member_bytes=1048576),server_writes=0,model_calls=0)
with (A/'scope.json').open('x') as f:json.dump(spec,f,indent=2)
source='SPEC='+repr(spec)+'''\nimport datetime,hashlib,json,os,socket,tarfile,time
from pathlib import Path
start=time.monotonic()
try:
 assert socket.gethostname()==SPEC['identity']['hostname'] and os.getuid()==SPEC['identity']['uid'],'current container identity mismatch'
 p=Path(SPEC['upload']['path'])
 assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file(),'archive type/link'
 assert p.stat().st_size==SPEC['upload']['bytes']<=SPEC['limits']['archive_bytes'],'archive size'
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==SPEC['upload']['sha256'],'archive SHA256'
 members=[]
 with tarfile.open(p,'r:gz') as t:
  items=t.getmembers();assert len(items)==2 and len({x.name for x in items})==2,'member count/duplicates'
  assert {x.name for x in items}=={r['member'] for r in SPEC['members']},'exact member names'
  for r in SPEC['members']:
   m=t.getmember(r['member']);assert m.isfile() and m.size==r['bytes']<=SPEC['limits']['member_bytes'],'member type/size'
   data=t.extractfile(m).read();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'member SHA256'
   members.append(dict(member=m.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 assert p.stat().st_size==len(raw) and hashlib.sha256(p.read_bytes()).hexdigest()==SPEC['upload']['sha256'],'archive changed during check'
 targets=[]
 for name in SPEC['targets']:
  target=Path(name);assert not any(x.is_symlink() for x in (target,*target.parents)),'target parent/link'
  targets.append(dict(path=name,exists=target.exists(),parent_exists=target.parent.is_dir()))
 assert time.monotonic()-start<=SPEC['limits']['wall_seconds'],'read-only budget'
 print(json.dumps(dict(status='UPLOAD_VERIFIED_READONLY_PASS',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),archive=SPEC['upload'],members=members,targets=targets,request_sha256=SPEC['request_sha256'],seconds=time.monotonic()-start,server_writes=0,installed_files=0,model_calls=0,execution_authorized=False)))
except BaseException as exc:
 print(json.dumps(dict(status='UPLOAD_VERIFY_FAILED_STOP',error=repr(exc),server_writes=0,model_calls=0)));raise
'''
payload=source.encode('utf-8');compile(payload,'readonly_upload_verification','exec')
with (A/'payload.py').open('xb') as f:f.write(payload)
template=N.parent/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=template.read_bytes();assert hashlib.sha256(driver).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
driver=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
with (A/'short_driver.py').open('xb') as f:f.write(driver)
with (A/'attempt_started.json').open('x') as f:json.dump(dict(payload_sha256=hashlib.sha256(payload).hexdigest(),scope_sha256=hashlib.sha256((A/'scope.json').read_bytes()).hexdigest(),server_writes=0),f)
command='import base64;exec(compile(base64.b64decode('+repr(base64.b64encode(driver).decode())+'),"<readonly_upload_check>","exec"))'
try:
 result=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/usr/bin/python3','-I','-S','-B','-c',command],input=json.dumps(dict(mode='execute_once',payload_base64=base64.b64encode(payload).decode())).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=155)
 cap=dict(returncode=result.returncode,timeout=False,stdout_base64=base64.b64encode(result.stdout).decode(),stderr_base64=base64.b64encode(result.stderr).decode())
except subprocess.TimeoutExpired as e:cap=dict(returncode=None,timeout=True,stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode())
with (A/'capture.json').open('x') as f:json.dump(cap,f,indent=2)
items=[]
for line in base64.b64decode(cap['stdout_base64']).decode(errors='replace').splitlines():
 try:item=json.loads(line)
 except ValueError:continue
 if isinstance(item,dict):items.append(item)
with (A/'events.json').open('x') as f:json.dump(items,f,indent=2)
report=next((x for x in reversed(items) if x.get('status') in ['UPLOAD_VERIFIED_READONLY_PASS','UPLOAD_VERIFY_FAILED_STOP']),None)
if report:
 with (A/'report.json').open('x') as f:json.dump(report,f,indent=2)
 print(json.dumps(report))
print(json.dumps(dict(returncode=cap['returncode'],timeout=cap['timeout'],report_received=report is not None)))
raise SystemExit(0 if cap['returncode']==0 and report and report['status']=='UPLOAD_VERIFIED_READONLY_PASS' else 1)
