from pathlib import Path
import ast,base64,hashlib,json
N=Path(__file__).resolve().parent;A=N/'authorized_execution_v2';A.mkdir(exist_ok=False)
S='ebb8d4051cc405939930a41fc292d55a81fe6cf5dc786c77a62b5a6317c46a4a'
def h(b):return hashlib.sha256(b).hexdigest()
def read_binding(r):
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'];return b
def save(n,b):
 with (A/n).open('xb') as f:f.write(b)
scope_raw=(N/'training_execution_request_v1.json').read_bytes();assert h(scope_raw)==S
scope=json.loads(scope_raw);qraw=read_binding(scope['entry_request']);q=json.loads(qraw)
acc=read_binding(scope['migration_acceptance'])
grant='已上传，单独授权该request，即可按冻结范围完成不覆盖安装、哈希核验和唯一一次16k训练。'
save('explicit_grant_v1.json',json.dumps(dict(user_text=grant,scope_sha256=S,training_attempts=1,no_retry=True),ensure_ascii=True,indent=2).encode())
text=read_binding(scope['local_serialization']['controller_template']).decode()
for marker,value in {'__EXECUTION_SCOPE_SHA256__':S,'__EXECUTION_SCOPE_RAW_BASE64__':base64.b64encode(scope_raw).decode(),'__ENTRY_REQUEST_RAW_BASE64__':base64.b64encode(qraw).decode(),'__MIGRATION_ACCEPTANCE_RAW_BASE64__':base64.b64encode(acc).decode(),'__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__':base64.b64encode(grant.encode()).decode()}.items():
 assert text.count(marker)==1;text=text.replace(marker,value)
tree=ast.parse(text)
for name,want in [('SCOPE_RAW',scope_raw),('Q_RAW',qraw),('ACCEPT_RAW',acc)]:
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==name for y in x.targets))
 assert base64.b64decode(node.value.args[0].value)==want
save('materialize_and_start_once_v1.py',text.encode())
mapping=read_binding(scope['minimal_deployment']['installation_mapping'])
pins=[*q['implementation'].values(),q['static_config'],q['order_plan'],q['GPU_audit'],q['preflight_scope'],q['resource_rebind'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
prefix="import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil\nfrom pathlib import Path\n"
prefix+='M=json.loads(base64.b64decode('+repr(base64.b64encode(mapping).decode())+'))\n'
prefix+='PINS='+repr(pins)+'\nREBIND='+repr(q['resource_rebind']['path'])+'\n'
prefix+='SCOPE_SHA='+repr(S)+'\nARCHIVE='+repr(scope['minimal_deployment']['future_upload_path'])+'\n'
prefix+='ARCHIVE_SIZE='+str(scope['minimal_deployment']['archive']['bytes'])+'\nARCHIVE_SHA='+repr(scope['minimal_deployment']['archive']['sha256'])+'\n'
body=r'''
START=time.monotonic();created=[];created_dirs=[];phase='IDENTITY';reads=0
PROJECT=Path(M['project']);DATA=Path(M['data_root']);DIRS=[Path(x) for x in M['directories']]
def need(ok,why):
 if not ok:raise RuntimeError(why)
def budget():need(time.monotonic()-START<100,'installation wall budget')
def parents(p,missing=False):
 for a in reversed(p.parents):
  if missing and not os.path.lexists(a):need(a in DIRS,'unlisted missing parent '+str(a));continue
  need(stat.S_ISDIR(a.lstat().st_mode),'linked/non-directory parent '+str(a))
def absent(p,missing=False):parents(p,missing);need(not os.path.lexists(p),'target already exists '+str(p))
def exact(r):
 global reads
 budget();p=Path(r['path']);parents(p);s=p.lstat()
 need(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and s.st_size<=100663296,'type/size '+str(p))
 b=p.read_bytes();reads+=len(b);need(reads<=536870912,'installation read budget')
 need((s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns),'changed '+str(p))
 need(hashlib.sha256(b).hexdigest()==r['sha256'],'hash '+str(p));return b
def dirfd(p):
 fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.parts[1:]:
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  return fd
 except BaseException:os.close(fd);raise
def event(d):print(json.dumps(d),flush=True)
def cmd(args):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()
try:
 identity=M['expected_identity'];need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU occupied')
 phase='ARCHIVE_AND_REUSE_BINDINGS'
 archive=exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 need(len(DIRS)==2 and DIRS==[DATA,DATA/'points'],'two exact directories')
 rows=M['files'];need(len(rows)==len({r['target'] for r in rows})==316,'exact316 targets')
 expected={r['archive_member']:r for r in rows};content={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  members=tf.getmembers();need(len(members)==len({x.name for x in members})==316 and {x.name for x in members}==set(expected),'exact archive members')
  for x in members:
   budget();rel=Path(x.name)
   need(x.isfile() and not rel.is_absolute() and '..' not in rel.parts and chr(92) not in x.name and x.size<=4194304,'member type/path/size')
   r=expected[x.name];p=Path(r['target'])
   need((x.name.startswith('points/') and p==DATA/x.name and p.parent==DATA/'points' and p.suffix=='.npz') or
        (x.name=='metadata/qualified_data_qc_foldC_16384_v1.json' and p==Path(M['reused_static']['path']).parent/'evidence/qualified_data_qc_foldC_16384_v1.json'),'mapped target')
   b=tf.extractfile(x).read();need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'member hash')
   content[p]=b
 for r in PINS:exact(r)
 rebind=json.loads(exact(next(r for r in PINS if r['path']==REBIND)));rr=dict(rebind['new_readonly_report']);rr['path']=str(Path(REBIND).parent/rr['path'])
 report=json.loads(exact(rr))
 for r in report['frozen_assets']['manifest']:exact(dict(path=r['path'],bytes=r['expected_bytes'],sha256=r['expected_sha256']))
 phase='ALL_TARGETS_ABSENT'
 for p in DIRS:absent(p,True)
 for p in content:absent(p,True)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk reserve')
 event(dict(status='DATA316_PREWRITE_PASS',scope_sha256=SCOPE_SHA,absent_targets=316,archive_SHA256=ARCHIVE_SHA,server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 for p in DIRS:
  absent(p);fd=dirfd(p.parent)
  try:os.mkdir(p.name,0o700,dir_fd=fd);created_dirs.append(str(p))
  finally:os.close(fd)
 for p,b in content.items():
  budget();absent(p);fd=dirfd(p.parent)
  try:
   child=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd);created.append(str(p))
   with os.fdopen(child,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
 phase='ALL_INSTALLED_HASHES'
 for r in rows:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
 need({p.name for p in (DATA/'points').iterdir()}=={Path(r['target']).name for r in rows if Path(r['target']).parent==DATA/'points'},'point file set')
 need({p.name for p in DATA.iterdir()}=={'points'},'data root set')
 event(dict(status='DATA316_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,installed_files=316,point_files=315,created_directories=created_dirs,installed_bytes=sum(len(b) for b in content.values()),hashed_bytes=reads,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created_files=created,created_directories=created_dirs,training_started=False));raise
'''
installer=prefix+body;compile(installer,'fixed16k_installer','exec');save('install_data316_once_v1.py',installer.encode())
driver=read_binding(scope['local_serialization']['short_driver_template'])
for stage,file in [('install','install_data316_once_v1.py'),('training','materialize_and_start_once_v1.py')]:
 payload=(A/file).read_bytes();rendered=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload).encode())
 compile(rendered,'fixed_short_driver','exec');save('invoke_'+stage+'_once_v1.py',rendered)
print(json.dumps(dict(status='AUTHORIZED_FROZEN_BYTES_PREPARED',scope_sha256=S,installer_bytes=len(installer.encode()),controller_bytes=len(text.encode()),server_operations=0)))
