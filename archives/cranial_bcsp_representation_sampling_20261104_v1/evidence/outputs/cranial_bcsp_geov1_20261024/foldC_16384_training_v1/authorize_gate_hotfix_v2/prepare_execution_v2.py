from pathlib import Path
import ast,base64,hashlib,json
N=Path(__file__).resolve().parent;A=N/'authorized_execution_v1';A.mkdir(exist_ok=False)
S='7221de1a48d700f3e2b90e3904689c9e63239832203356785e8cd0f2278de2fd'
def h(raw):return hashlib.sha256(raw).hexdigest()
def bound(r):
 raw=Path(r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256'];return raw
def save(n,raw):
 with (A/n).open('xb') as f:f.write(raw)
raw=(N/'training_execution_request_v2.json').read_bytes();assert h(raw)==S
s=json.loads(raw);qraw=bound(s['entry_request']);q=json.loads(qraw);acc=bound(s['migration_acceptance'])
grant='下一步单独授权v2 request完整SHA256'
save('explicit_grant_v1.json',json.dumps(dict(user_text=grant,scope_sha256=S,training_attempts=1,no_retry=True),ensure_ascii=True,indent=2).encode())
controller=bound(s['local_serialization']['controller_template']).decode()
for marker,value in {'__EXECUTION_SCOPE_SHA256__':S,'__EXECUTION_SCOPE_RAW_BASE64__':base64.b64encode(raw).decode(),'__ENTRY_REQUEST_RAW_BASE64__':base64.b64encode(qraw).decode(),'__MIGRATION_ACCEPTANCE_RAW_BASE64__':base64.b64encode(acc).decode(),'__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__':base64.b64encode(grant.encode()).decode()}.items():
 assert controller.count(marker)==1;controller=controller.replace(marker,value)
tree=ast.parse(controller)
for name,want in [('SCOPE_RAW',raw),('Q_RAW',qraw),('ACCEPT_RAW',acc)]:
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets))
 assert base64.b64decode(node.value.args[0].value)==want
save('materialize_and_start_once_v1.py',controller.encode())
mapping=bound(s['minimal_deployment']['installation_mapping'])
previous=(N.parent/'authorized_execution_v2/install_data316_once_v1.py').read_text()
tree=ast.parse(previous);names={'need','budget','parents','absent','exact','dirfd','event','cmd'}
helpers='\n\n'.join(ast.get_source_segment(previous,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
pins=[q['implementation']['runtime'],q['implementation']['preflight_helper'],q['static_config'],q['order_plan'],q['GPU_audit'],q['preflight_scope'],q['resource_rebind'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
prefix='import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil\nfrom pathlib import Path\n'
prefix+='M=json.loads(base64.b64decode('+repr(base64.b64encode(mapping).decode())+'))\n'
prefix+='PINS='+repr(pins)+'\n'
prefix+='ARCHIVE='+repr(s['minimal_deployment']['future_upload_path'])+'\nARCHIVE_SIZE='+str(s['minimal_deployment']['archive']['bytes'])+'\nARCHIVE_SHA='+repr(s['minimal_deployment']['archive']['sha256'])+'\n'
prefix+='SCOPE_SHA='+repr(S)+"\nSTART=time.monotonic();created=[];phase='IDENTITY';reads=0;DIRS=[]\nPROJECT=Path(M['expected_identity']['project']);CODE=Path(M['code_root'])\n"
body='''
try:
 identity=M['expected_identity'];need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU occupied')
 phase='UPLOAD_AND_EXISTING_ASSETS'
 archive=exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 rows=M['files'];need(len(rows)==len({x['target'] for x in rows})==2 and not M['new_directories'],'exact two files,no directories')
 expected={r['archive_member']:r for r in rows};content={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  ms=tf.getmembers();need(len(ms)==len({x.name for x in ms})==2 and {x.name for x in ms}==set(expected),'exact members')
  for x in ms:
   need(x.isfile() and '/' not in x.name and chr(92) not in x.name and x.size<=65536,'member type/path/size')
   r=expected[x.name];p=Path(r['target']);need(p==CODE/x.name,'exact target')
   b=tf.extractfile(x).read();need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'member hash');content[p]=b
 for r in PINS:exact(r)
 phase='ALL_TARGETS_ABSENT'
 for p in content:absent(p)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk reserve')
 event(dict(status='TWO_FILE_PREWRITE_PASS',scope_sha256=SCOPE_SHA,targets=2,server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 for p,b in content.items():
  absent(p);fd=dirfd(p.parent)
  try:
   child=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd);created.append(str(p))
   with os.fdopen(child,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
 for r in rows:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
 event(dict(status='TWO_FILE_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,created=created,reinstalled_data_files=0,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created=created,training_started=False));raise
'''
installer=prefix+helpers+'\n'+body;compile(installer,'two_file_installation','exec');save('install_two_once_v1.py',installer.encode())
driver=bound(s['local_serialization']['short_driver_template'])
for stage,file in [('install','install_two_once_v1.py'),('training','materialize_and_start_once_v1.py')]:
 payload=(A/file).read_bytes();rendered=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload).encode())
 compile(rendered,'short_driver','exec');save('invoke_'+stage+'_once_v1.py',rendered)
print(json.dumps(dict(status='AUTHORIZED_BYTES_AND_STATIC_CHECKS_PASS',scope_sha256=S,installer_bytes=len(installer.encode()),controller_bytes=len(controller.encode()),server_operations=0)))
