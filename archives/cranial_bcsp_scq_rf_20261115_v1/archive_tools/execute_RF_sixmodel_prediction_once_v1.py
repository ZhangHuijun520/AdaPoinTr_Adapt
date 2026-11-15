"""Hash-bound exclusive deployment and one authorized630 Native submission."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,shlex,subprocess,sys,zlib
R=Path(__file__).resolve().parent.parent
S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1'
B=S/'pending_request_v1';O=B/'authorized_execution_v1'
RH='b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def jb(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save(p,v):
 with p.open('xb') as f:f.write(jb(v))
Q=B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json';assert sha(Q)==RH
q=read(Q);mpath=B/'installation_mapping_v1.json';mp=read(mpath);delivery=read(B/'delivery_receipt_v1.json')
archive=Path(delivery['archive']['path']);assert sha(archive)==delivery['archive']['sha256']
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
for r in mp['files']:assert sha(B/r['member'])==r['sha256'] and (B/r['member']).stat().st_size==r['bytes']
index=read(B/'payload/RF_sixmodel_input_index_v1.json');I=q['identity'];L=q['launch_contract'];C=mp['remote_root'];AR='/home/jovyan/'+archive.name
spec=importlib.util.spec_from_file_location('scq_prediction_launcher_only',S/'bcsp_scq_rf_sixmodel_native_predict_v1.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
auth=dict(schema='bcsp-development-authorization-v1',request_sha256=RH,explicit_user_authorization=True,user_authorization_text='用户确认已上传，单独授权上一条完整SHA256对应的不覆盖安装与唯一一次630次Native预测；完整SHA256：'+RH)
ab=jb(auth);ah=hashlib.sha256(ab).hexdigest();runtime=dict(schema='bcsp-development-runtime-v1',request_sha256=RH,authorization_sha256=ah);rb=jb(runtime);rhash=hashlib.sha256(rb).hexdigest();lb=entry.render_launcher(q,RH,ah,rhash).encode('utf-8')
controls=[(L['authorization'],ab),(L['runtime'],rb),(L['launcher'],lb)]
scripts=[]
def add(label,source,values,seconds=60):
 class Bind(ast.NodeTransformer):
  def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
 code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(source))));ast.parse(code,feature_version=(3,8));compile(code,label,'exec')
 blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(blob)+')))'])
 assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 assert zlib.decompress(base64.b64decode(blob)).decode()==code
 scripts.append((label,code,cmd,seconds))
add('identity_resources','''from pathlib import Path
import socket,os,subprocess,shutil,json
assert socket.gethostname()==HOST and os.getuid()==1000
p=Path(PROJECT);root=Path(ROOT);out=Path(OUT)
assert p.is_dir() and p.resolve()==p and root.parent.is_dir() and out.parent.is_dir()
for x in [root,out]:assert not x.exists() and not any(z.is_symlink() for z in (x,*x.parents)),str(x)
assert shutil.disk_usage(p).free>=4294967296
assert subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
g=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip();a=[x.strip() for x in g.split(',')]
assert a[:4]==GPU and int(a[4])<=256,a
assert str(Path(PYTHON).resolve())==PYTHON
v=subprocess.check_output([PYTHON,'-I','-S','-B','-c','import sys;print(sys.version.split()[0])'],text=True,timeout=10).strip();assert v==VERSION
print(json.dumps(dict(status='FRESH_IDENTITY_RESOURCES_NEW_ROOT_PASS',hostname=socket.gethostname(),GPU=a,free_disk=shutil.disk_usage(p).free,python_version=v)))
''',dict(HOST=I['hostname'],PROJECT=I['project'],ROOT=C,OUT=q['output'],SESSION=L['tmux_session'],GPU=[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])],PYTHON=I['python_realpath'],VERSION=I['python_version']))
add('upload','''from pathlib import Path
import hashlib,tarfile,json,socket
assert socket.gethostname()==HOST
p=Path(ARCHIVE);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
h=lambda b:hashlib.sha256(b).hexdigest()
assert p.stat().st_size==SIZE and h(p.read_bytes())==DIGEST
for s in ['.sha256','.bytes','.contents.sha256']:assert Path(str(p)+s).is_file() and not Path(str(p)+s).is_symlink()
assert Path(str(p)+'.sha256').read_text().split()[0]==DIGEST and int(Path(str(p)+'.bytes').read_text())==SIZE
expected={l.split(None,1)[1]:l.split(None,1)[0] for l in Path(str(p)+'.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
 ms=t.getmembers();assert len(ms)==len(expected)==17 and len({m.name for m in ms})==17
 for m in ms:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.size<4194304
  assert m.name in expected and h(t.extractfile(m).read())==expected[m.name]
 assert h(t.extractfile('installation_mapping_v1.json').read())==MAPSHA
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS',members=17)))
''',dict(HOST=I['hostname'],ARCHIVE=AR,SIZE=archive.stat().st_size,DIGEST=sha(archive),MAPSHA=sha(mpath)))
bindings={r['path']:r for r in mp['reused_readonly_bindings']}
# Include exact project/config/provider sources already frozen by the admitted scope.
mirror=read(B/'local_mirror_v1.json')
scopepath=R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json'
assert sha(scopepath)==q['preflight_scope']['sha256'] and scopepath.stat().st_size==q['preflight_scope']['bytes']
scope=read(scopepath)
helperpath=Path(mirror[q['helper']['path']]);sp=importlib.util.spec_from_file_location('scq_bound_source_map',helperpath);helper=importlib.util.module_from_spec(sp);sp.loader.exec_module(helper)
for rel,r in helper.source_map(scope).items():bindings[q['model_root']+'/'+rel]=dict(r,path=q['model_root']+'/'+rel)
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:bindings[r['path']]=r
config=scope['bindings']['base_config'];bindings[q['model_root']+'/base_model.yaml']=dict(config,path=q['model_root']+'/base_model.yaml')
hash_source='''from pathlib import Path
import socket,hashlib,json
assert socket.gethostname()==HOST
total=0
for r in ROWS:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'];before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b);total+=len(b)
 after=p.stat();assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert h.hexdigest()==r['sha256'],str(p)
print(json.dumps(dict(status='EXACT_HASHES_PASS',files=len(ROWS),hashed_bytes=total)))
'''
rows=list(bindings.values())
for i in range(0,len(rows),4):add('asset_'+str(i),hash_source,dict(HOST=I['hostname'],ROWS=rows[i:i+4]))
for run in index['runs']:add('checkpoint_'+run['label'],hash_source,dict(HOST=I['hostname'],ROWS=[run['checkpoint']]))
add('inputs210','''from pathlib import Path
import socket,hashlib,tarfile,json
assert socket.gethostname()==HOST
p=Path(ARCHIVE);assert hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
with tarfile.open(p) as t:
 index=json.loads(t.extractfile('payload/RF_sixmodel_input_index_v1.json').read())
records={r['input']['path']:r['input'] for r in index['inputs']};assert len(index['inputs'])==630 and len(records)==210
total=0
for r in records.values():
 p=Path(r['path']);assert p.suffix=='.npz' and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes']
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);total+=len(b)
 assert h.hexdigest()==r['sha256'],str(p)
print(json.dumps(dict(status='ALL210_INPUT_HASHES_PASS',files=210,occurrences=630,hashed_bytes=total,array_reads=0)))
''',dict(HOST=I['hostname'],ARCHIVE=AR,DIGEST=sha(archive)))
add('exclusive_install','''from pathlib import Path
import socket,os,hashlib,tarfile,json
assert socket.gethostname()==HOST and os.getuid()==1000
root=Path(ROOT);out=Path(OUT);p=Path(ARCHIVE)
for x in [root,out]:assert not x.exists() and not any(z.is_symlink() for z in (x,*x.parents))
assert root.parent.is_dir() and out.parent.is_dir() and hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
with tarfile.open(p) as t:
 data=t.extractfile('installation_mapping_v1.json').read();assert hashlib.sha256(data).hexdigest()==MAPSHA
 m=json.loads(data);rows=m['files'];assert len(rows)==16
 for r in rows:
  target=Path(r['target']);assert target.parent==root and not target.exists() and not target.is_symlink()
  b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 root.mkdir(mode=448)
 for r in rows:
  target=Path(r['target']);b=t.extractfile(r['member']).read()
  with target.open('xb') as f:f.write(b)
  assert target.stat().st_size==r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==r['sha256']
 (root/'control').mkdir(mode=448)
print(json.dumps(dict(status='SIXTEEN_FILES_EXCLUSIVE_INSTALL_PASS',files=16)))
''',dict(HOST=I['hostname'],ROOT=C,OUT=q['output'],ARCHIVE=AR,DIGEST=sha(archive),MAPSHA=sha(mpath)))
for i,(path,data) in enumerate(controls):
 add('control_'+str(i),'''from pathlib import Path
import socket,base64,hashlib,json,zlib
assert socket.gethostname()==HOST
p=Path(TARGET);assert p.parent.is_dir() and not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
b=zlib.decompress(base64.b64decode(DATA));assert hashlib.sha256(b).hexdigest()==DIGEST
with p.open('xb') as f:f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS',bytes=len(b))))
''',dict(HOST=I['hostname'],TARGET=path,DATA=base64.b64encode(zlib.compress(data,9)).decode(),DIGEST=hashlib.sha256(data).hexdigest()))
add('installed_authorize','''from pathlib import Path
import socket,hashlib,importlib.util,json
assert socket.gethostname()==HOST
p=Path(ENTRY);assert hashlib.sha256(p.read_bytes()).hexdigest()==ENTRYSHA
s=importlib.util.spec_from_file_location('installed_scq_authorize',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def rec(p,h):return dict(path=p,bytes=Path(p).stat().st_size,sha256=h)
q=m.authorize(rec(REQUEST,REQUESTSHA),rec(AUTH,AUTHSHA),rec(RUNTIME,RUNTIMESHA))
index=m.bound(q['input_index']);runs,rows=m.validate_index(index,m.bound(q['fold_binding']))
m.validate_source(index,None,[json.loads(x) for x in m.exact(q['source_manifest']).read_text().splitlines()]);m.validate_evidence(q,index)
assert len(runs)==6 and len(rows)==630
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS',forwards=630,model_calls=0)))
''',dict(HOST=I['hostname'],ENTRY=q['entry']['path'],ENTRYSHA=q['entry']['sha256'],REQUEST=L['request_path'],REQUESTSHA=RH,AUTH=L['authorization'],AUTHSHA=ah,RUNTIME=L['runtime'],RUNTIMESHA=rhash))
add('single_launch','''from pathlib import Path
import socket,os,subprocess,hashlib,shutil,json
assert socket.gethostname()==HOST and os.getuid()==1000
out=Path(OUT);claim=Path(CLAIM)
for p in [out,claim]:assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
assert subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
g=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip();a=[x.strip() for x in g.split(',')]
assert a[:4]==GPU and int(a[4])<=256 and shutil.disk_usage(out.parent).free>=4294967296
for p,h in CONTROLS:assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h and not Path(p).is_symlink()
with claim.open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=REQUESTSHA),f)
x=subprocess.run(['tmux','new-session','-d','-s',SESSION,'bash '+shlex_quote]);assert x.returncode==0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED',session=SESSION,forwards=630)))
''',dict(HOST=I['hostname'],OUT=q['output'],CLAIM=q['launch_attempt'],SESSION=L['tmux_session'],GPU=[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])],CONTROLS=[(p,hashlib.sha256(b).hexdigest()) for p,b in controls],REQUESTSHA=RH,shlex_quote=shlex.quote(L['launcher'])))
scripts.sort(key=lambda row: 0 if row[0]=='identity_resources' else 1 if row[0]=='upload' else 2 if row[0]=='inputs210' else 3)
if '--static' in sys.argv:
 d=B/'preexecution_static_v1';d.mkdir()
 for label,code,cmd,seconds in scripts:
  with (d/(label+'.remote.py')).open('x',encoding='utf-8',newline='\n') as f:f.write(code)
 save(d/'review_v1.json',dict(status='ALL_REMOTE_SCRIPTS_STATIC_PASS',scripts=len(scripts),maximum_command_bytes=max(len(v[2].encode()) for v in scripts),controller_sha256=sha(Path(__file__)),request_sha256=RH,server_calls=0,execution_controls_materialized=False))
 print(json.dumps(dict(status='ALL_REMOTE_SCRIPTS_STATIC_PASS',scripts=len(scripts),max_bytes=max(len(v[2].encode()) for v in scripts))))
else:
 assert read(B/'preexecution_static_v1/review_v1.json')['controller_sha256']==sha(Path(__file__))
 O.mkdir();stage='begin'
 try:
  for label,code,cmd,seconds in scripts:
   stage=label
   if label=='control_0':
    for name,data in [('authorization_v1.json',ab),('runtime_v1.json',rb),('launch_once_v1.sh',lb)]:
     with (O/name).open('xb') as f:f.write(data)
   x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(seconds),'--',cmd],capture_output=True,timeout=seconds+15)
   for suffix,data in [('stdout',x.stdout),('stderr',x.stderr)]:
    with (O/(label+'_'+suffix+'.bin')).open('xb') as f:f.write(data)
   assert x.returncode==0,(label,x.returncode,x.stdout.decode(errors='replace')[-1800:])
   result=json.loads(x.stdout);save(O/(label+'.json'),result)
   print(json.dumps(dict(stage=label,status=result['status'])),flush=True)
  save(O/'launch_receipt_v1.json',dict(status='SINGLE_AUTHORIZED_630_PREDICTION_SUBMITTED',request_sha256=RH,output=q['output'],session=L['tmux_session'],forward_budget=630,no_retry=True))
 except BaseException as exc:
  save(O/'stop_receipt_v1.json',dict(status='STOPPED_NO_AUTOMATIC_RETRY',stage=stage,error=repr(exc),request_sha256=RH));raise
