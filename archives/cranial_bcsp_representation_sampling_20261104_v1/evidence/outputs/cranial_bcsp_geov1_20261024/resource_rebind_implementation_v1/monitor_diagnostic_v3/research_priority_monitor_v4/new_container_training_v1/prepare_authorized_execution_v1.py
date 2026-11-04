from pathlib import Path
import ast,base64,hashlib,json
N=Path(__file__).resolve().parent
A=N/'authorized_execution_v1';A.mkdir(exist_ok=False)
BASE=next(p for p in N.parents if p.name=='mamba-ccf-c-1-high-resolution')
R=BASE/'outputs/cranial_bcsp_geov1_20261024/resource_rebind_implementation_v1'
T=R/'first_training_request_foldC_8192_v1/local_byte_serialization_v2'
S='16655f4494fe2458619129958a370d240866a15b339ec2d40b595d827b675f0a'
def h(b):return hashlib.sha256(b).hexdigest()
def save(name,raw):
 with (A/name).open('xb') as f:f.write(raw)
def b64(b):return base64.b64encode(b).decode()
scope_raw=(N/'training_execution_request_v4.json').read_bytes();assert h(scope_raw)==S
scope=json.loads(scope_raw)
q=(N/'training_entry_request_v4.json').read_bytes();acc=(N/'migration_uncertainty_current_device_v2.json').read_bytes()
for key,raw in [('entry_request',q),('migration_acceptance',acc)]:assert h(raw)==scope[key]['sha256'] and len(raw)==scope[key]['bytes']
grant='已上传，单独授权上述完整哈希'
save('explicit_user_grant_v1.json',json.dumps(dict(user_text=grant,execution_scope_sha256=S,scope='Six exclusive installed files plus one fresh training launch; no retry/resume'),ensure_ascii=True,indent=2).encode())
controller=(T/'controller_template_v2.py').read_bytes()
assert h(controller)==scope['local_serialization']['controller_template']['sha256']
text=controller.decode()
for marker,value in {'__EXECUTION_SCOPE_SHA256__':S,'__EXECUTION_SCOPE_RAW_BASE64__':b64(scope_raw),'__ENTRY_REQUEST_RAW_BASE64__':b64(q),'__MIGRATION_ACCEPTANCE_RAW_BASE64__':b64(acc),'__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__':b64(grant.encode())}.items():
 assert text.count(marker)==1;text=text.replace(marker,value)
tree=ast.parse(text)
for name,want in [('SCOPE_RAW',scope_raw),('Q_RAW',q),('ACCEPT_RAW',acc)]:
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets))
 assert base64.b64decode(node.value.args[0].value)==want
save('materialize_and_start_once_v1.py',text.encode())
mapping=(N/'minimal_installation_mapping_v1.json').read_bytes()
assert h(mapping)==scope['minimal_deployment']['installation_mapping']['sha256']
# Reuse the already-reviewed filesystem helpers without modifying them.
old=(R/'monitor_diagnostic_v3/authorized_installation_v1/install_overlay_once_v1.py').read_text()
tree=ast.parse(old)
names={'need','sha','event','budget','parents','absent','read_exact','dirfd'}
helpers='\n\n'.join(ast.get_source_segment(old,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
prefix="""import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil
from pathlib import Path
START=time.monotonic();created=[];created_dirs=[];phase='IDENTITY'
"""
prefix+='M=json.loads(base64.b64decode('+repr(b64(mapping))+'))\n'
prefix+='SCOPE_SHA='+repr(S)+'\n'
prefix+='ARCHIVE='+repr(scope['minimal_deployment']['future_upload_path'])+'\n'
prefix+='ARCHIVE_SIZE='+str(scope['minimal_deployment']['archive']['bytes'])+'\n'
prefix+='ARCHIVE_SHA='+repr(scope['minimal_deployment']['archive']['sha256'])+'\n'
prefix+="NEW_DIR=Path(M['new_directory']);PROJECT=Path(M['project'])\n"
body="""
try:
 identity=M['expected_identity']
 need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 def cmd(args):
  p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True)
  return p.stdout.decode().strip()
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU not idle')
 phase='ARCHIVE_AND_EXISTING_ASSETS'
 archive=read_exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 rows=M['files'];need(len(rows)==len({x['target'] for x in rows})==6,'six targets')
 content={};expected={x['archive_member']:x for x in rows}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  ms=tf.getmembers();need(len(ms)==len({x.name for x in ms})==6 and {x.name for x in ms}==set(expected),'members')
  for x in ms:
   need(x.isfile() and '/' not in x.name and '\\\\' not in x.name and x.size<=262144,'member type/path/size')
   r=expected[x.name];raw=tf.extractfile(x).read();need(len(raw)==r['bytes'] and sha(raw)==r['sha256'],'member hash')
   target=Path(r['target']);need(target.parent in [NEW_DIR,NEW_DIR.parent.parent],'exact installation boundary')
   content[target]=raw
 report=json.loads(next(raw for p,raw in content.items() if p.name=='readonly_identity_assets_01dt08_v1.json'))
 for r in report['frozen_assets']['manifest']:
  read_exact(dict(path=r['path'],bytes=r['expected_bytes'],sha256=r['expected_sha256']))
 phase='ALL_TARGETS_ABSENT'
 absent(NEW_DIR)
 for p in content:absent(p,allow_missing=True)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk')
 event(dict(status='SIX_FILE_PREWRITE_PASS',scope_sha256=SCOPE_SHA,targets=6,selected_assets=30,server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 fd=dirfd(NEW_DIR.parent)
 try:os.mkdir(NEW_DIR.name,0o700,dir_fd=fd);created_dirs.append(str(NEW_DIR))
 finally:os.close(fd)
 for p,raw in content.items():
  absent(p);fd=dirfd(p.parent)
  try:
   child=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd);created.append(str(p))
   with os.fdopen(child,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
 for r in rows:read_exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
 need(set(p.name for p in NEW_DIR.iterdir())=={Path(r['target']).name for r in rows if Path(r['target']).parent==NEW_DIR},'evidence set')
 event(dict(status='SIX_FILE_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,created=created,directories=created_dirs,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created=created,directories=created_dirs,training_started=False));raise
"""
installer=prefix+'\n'+helpers+'\n'+body
compile(installer,'installer','exec');save('install_six_once_v1.py',installer.encode())
for name,payloadname in [('install','install_six_once_v1.py'),('training','materialize_and_start_once_v1.py')]:
 payload=(A/payloadname).read_bytes()
 driver=(T/'short_driver_template_v2.py').read_bytes();assert h(driver)==scope['local_serialization']['short_driver_template']['sha256']
 rendered=driver.decode().replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload))
 compile(rendered,'short_driver','exec');save('invoke_'+name+'_once_v1.py',rendered.encode())
print(json.dumps(dict(status='AUTHORIZED_BYTES_AND_PAYLOADS_PREPARED',scope_sha256=S,installer_bytes=len(installer.encode()),controller_bytes=len(text.encode()),server_operations=0)))
