from pathlib import Path
import ast,base64,hashlib,json
N=Path(__file__).resolve().parent;A=N/'authorized_execution_v1';A.mkdir(exist_ok=False)
S='1b2439ab16886af2452fce5a6474729bee291d9961df15ca480a3a839790eea1'
def h(b):return hashlib.sha256(b).hexdigest()
def bound(r):
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256'];return b
def save(name,b):
 with (A/name).open('xb') as f:f.write(b)
raw=(N/'training_execution_request_v1.json').read_bytes();assert h(raw)==S
s=json.loads(raw);qraw=bound(s['entry_request']);q=json.loads(qraw);acc=bound(s['migration_acceptance'])
grant='已上传，单独授权该request，即可按冻结范围完成不覆盖安装、哈希核验及唯一一次Fold D训练。'
save('explicit_grant_v1.json',json.dumps(dict(user_text=grant,scope_sha256=S,training_attempts=1,no_retry=True),ensure_ascii=True,indent=2).encode())
text=bound(s['local_serialization']['controller_template']).decode()
for marker,value in {'__EXECUTION_SCOPE_SHA256__':S,'__EXECUTION_SCOPE_RAW_BASE64__':base64.b64encode(raw).decode(),'__ENTRY_REQUEST_RAW_BASE64__':base64.b64encode(qraw).decode(),'__MIGRATION_ACCEPTANCE_RAW_BASE64__':base64.b64encode(acc).decode(),'__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__':base64.b64encode(grant.encode()).decode()}.items():
 assert text.count(marker)==1;text=text.replace(marker,value)
tree=ast.parse(text)
for name,want in [('SCOPE_RAW',raw),('Q_RAW',qraw),('ACCEPT_RAW',acc)]:
 node=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in x.targets))
 assert base64.b64decode(node.value.args[0].value)==want
save('materialize_and_start_once_v1.py',text.encode())
mapping=bound(s['minimal_deployment']['installation_mapping'])
old=(N.parent/'foldC_16384_training_v1/authorized_execution_v2/install_data316_once_v1.py').read_text();tree=ast.parse(old)
names={'need','budget','parents','absent','exact','dirfd','event','cmd'}
helpers='\n\n'.join(ast.get_source_segment(old,x) for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names)
pins=[q['implementation']['runtime'],q['implementation']['preflight_helper'],q['static_config'],q['GPU_audit'],q['preflight_scope'],q['resource_rebind'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values()]
codepins=[q['implementation']['entry'],q['implementation']['contract'],q['order_plan'],q['QC']['qualified_receipt']]
prefix='import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil\nfrom pathlib import Path\n'
prefix+='M=json.loads(base64.b64decode('+repr(base64.b64encode(mapping).decode())+'))\n'
prefix+='PINS='+repr(pins)+'\nCODEPINS='+repr(codepins)+'\nREBIND='+repr(q['resource_rebind']['path'])+'\n'
prefix+='ARCHIVE='+repr(s['minimal_deployment']['future_upload_path'])+'\nARCHIVE_SIZE='+str(s['minimal_deployment']['archive']['bytes'])+'\nARCHIVE_SHA='+repr(s['minimal_deployment']['archive']['sha256'])+'\nSCOPE_SHA='+repr(S)+'\n'
prefix+="START=time.monotonic();created=[];created_dirs=[];phase='IDENTITY';reads=0\nPROJECT=Path(M['project']);DATA=Path(M['data_root']);CODE=Path(M['code_root']);DIRS=[Path(p) for p in M['directories']]\n"
body='''
try:
 identity=M['expected_identity'];need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU occupied')
 phase='UPLOAD_AND_REUSED_BINDINGS'
 archive=exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 rows=M['files'];need(len(rows)==len({r['target'] for r in rows})==319 and DIRS==[DATA,DATA/'points'],'exact319 files/two directories')
 expected={r['archive_member']:r for r in rows};content={};allowed_code={r['path'] for r in CODEPINS}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  members=tf.getmembers();need(len(members)==len({x.name for x in members})==319 and {x.name for x in members}==set(expected),'exact archive members')
  for x in members:
   budget();rel=Path(x.name);need(x.isfile() and not rel.is_absolute() and '..' not in rel.parts and chr(92) not in x.name and x.size<=4194304,'member type/path/size')
   r=expected[x.name];p=Path(r['target'])
   need((x.name.startswith('points/') and p==DATA/x.name and p.parent==DATA/'points' and p.suffix=='.npz') or
        (x.name.startswith('code/') and str(p) in allowed_code and p.name==rel.name),'exact mapped target')
   b=tf.extractfile(x).read();need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'member hash');content[p]=b
 for r in CODEPINS:
  b=content[Path(r['path'])];need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'code/QC/order request pin')
 for r in PINS:exact(r)
 rebind=json.loads(exact(next(r for r in PINS if r['path']==REBIND)));rr=dict(rebind['new_readonly_report']);rr['path']=str(Path(REBIND).parent/rr['path'])
 report=json.loads(exact(rr))
 for r in report['frozen_assets']['manifest']:exact(dict(path=r['path'],bytes=r['expected_bytes'],sha256=r['expected_sha256']))
 phase='ALL_TARGETS_ABSENT'
 for p in DIRS:absent(p,True)
 for p in content:absent(p,True)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk reserve')
 event(dict(status='FOLDD319_PREWRITE_PASS',scope_sha256=SCOPE_SHA,absent_targets=319,server_writes=0))
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
 need({p.name for p in (DATA/'points').iterdir()}=={Path(r['target']).name for r in rows if Path(r['target']).parent==DATA/'points'},'315 point file set')
 need({p.name for p in DATA.iterdir()}=={'points'},'data root set')
 event(dict(status='FOLDD319_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,installed_files=319,point_files=315,created_directories=created_dirs,installed_bytes=sum(map(len,content.values())),hashed_bytes=reads,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created_files=created,created_directories=created_dirs,training_started=False));raise
'''
installer=prefix+helpers+'\n'+body;compile(installer,'FoldD319installer','exec');save('install_foldD319_once_v1.py',installer.encode())
driver=bound(s['local_serialization']['short_driver_template'])
for stage,file in [('install','install_foldD319_once_v1.py'),('training','materialize_and_start_once_v1.py')]:
 payload=(A/file).read_bytes();rendered=driver.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload).encode());compile(rendered,'short_driver','exec')
 save('invoke_'+stage+'_once_v1.py',rendered)
print(json.dumps(dict(status='AUTHORIZED_BYTES_AND_STATIC_CHECKS_PASS',scope_sha256=S,installer_bytes=len(installer.encode()),controller_bytes=len(text.encode()),server_operations=0)))
