"""Authorized RF CUDA installation and one tmux attempt; short byte-preserving calls."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,shlex,subprocess,sys,zlib

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_cuda_preparation_20261114_v1'
T=B/'pending_transport_v1'
O=B/'authorized_execution_v1'
RH='85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def jb(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def save(p,v):
    with p.open('xb') as f:f.write(jb(v))


Q=T/'payload/SCQ_RF_artificial_cuda_execution_request_v1.json'
assert sha(Q)==RH
q=read(Q);mapping=T/'installation_mapping_v1.json';mp=read(mapping);delivery=read(B/'pending_delivery_v1.json')
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
assert mp['request_sha256']==RH and len(mp['files'])==12
for row in mp['files']:
    p=T/row['member'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
archive=Path(delivery['archive']['path']);assert sha(archive)==delivery['archive']['sha256']
I=q['identity'];L=q['launch_contract'];C=mp['remote_root'];AR='/home/jovyan/'+archive.name
spec=importlib.util.spec_from_file_location('RF_launcher_renderer_only',B/'bcsp_scq_rf_cuda_admission_v1.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
auth=dict(schema='bcsp-scq-rf-cuda-authorization-v1',request_sha256=RH,explicit_user_authorization=True,
          user_authorization_text='已上传，单独授权上述哈希。上下文完整SHA256：'+RH)
ab=jb(auth);ah=hashlib.sha256(ab).hexdigest()
runtime=dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256=RH,authorization_sha256=ah)
rb=jb(runtime);rhash=hashlib.sha256(rb).hexdigest()
entry.authorize(q,RH,auth,ah,runtime)
lb=entry.render_launcher(q,RH,ah,rhash).encode('utf-8')
controls=[(L['authorization_path'],ab),(L['runtime_path'],rb),(L['launcher_path'],lb)]
scripts=[]


def add(label,source,values,seconds=60):
    class Bind(ast.NodeTransformer):
        def visit_Name(self,n):
            return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
    code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(source))))
    ast.parse(code,feature_version=(3,8));compile(code,label,'exec')
    blob=base64.b64encode(zlib.compress(code.encode('utf-8'),9)).decode()
    command=shlex.join(['/usr/bin/python3','-I','-S','-B','-c',"import zlib,base64;exec(zlib.decompress(base64.b64decode("+repr(blob)+")))"])
    assert len(command.encode())<=2048,(label,len(command.encode()))
    assert zlib.decompress(base64.b64decode(blob)).decode()==code
    scripts.append((label,code,command,seconds))


add('identity_resources','''from pathlib import Path
import os,socket,subprocess,shutil,json
assert socket.gethostname()==HOST and os.getuid()==1000,dict(expected=HOST,observed=socket.gethostname(),uid=os.getuid())
project=Path(PROJECT);root=Path(ROOT);out=Path(OUT)
assert project.is_dir() and project.resolve()==project
os.chdir(project)
for p in [root,out]:assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
assert root.parent.is_dir() and out.parent.is_dir() and shutil.disk_usage(project).free>=4294967296
assert subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
a=[x.strip() for x in subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
assert a[:4]==GPU and int(a[4])<=256,a
assert Path(PYTHON).resolve()==Path(PYTHON)
v=subprocess.check_output([PYTHON,'-I','-S','-B','-c','import sys;print(sys.version.split()[0])'],text=True,timeout=10).strip();assert v==VERSION
git=subprocess.run(['git','status','--short','--branch'],capture_output=True,text=True,timeout=10)
print(json.dumps(dict(status='FRESH_IDENTITY_RESOURCES_ABSENT_ROOT_PASS',hostname=socket.gethostname(),uid=os.getuid(),project=os.getcwd(),GPU=a,free_disk=shutil.disk_usage(project).free,python_version=v,git_status=git.stdout[:1000],git_returncode=git.returncode)))
''',dict(HOST=I['hostname'],PROJECT=q['project'],ROOT=C,OUT=q['output'],SESSION=L['tmux_session'],GPU=[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])],PYTHON=I['python_realpath'],VERSION=I['python_version']))
add('upload','''from pathlib import Path
import hashlib,tarfile,json,socket
assert socket.gethostname()==HOST
p=Path(ARCHIVE);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
h=lambda b:hashlib.sha256(b).hexdigest()
assert p.stat().st_size==SIZE and h(p.read_bytes())==DIGEST
for s in ['.sha256','.bytes','.contents.sha256']:assert Path(str(p)+s).is_file() and not Path(str(p)+s).is_symlink()
assert Path(str(p)+'.sha256').read_text().split()[0]==DIGEST and int(Path(str(p)+'.bytes').read_text())==SIZE
lines=Path(str(p)+'.contents.sha256').read_text().splitlines();expected={l.split(None,1)[1]:l.split(None,1)[0] for l in lines}
assert len(lines)==len(expected)==13
with tarfile.open(p) as t:
 ms=t.getmembers();assert len(ms)==13 and len({m.name for m in ms})==13 and set(expected)=={m.name for m in ms}
 for m in ms:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.size<4194304
  assert h(t.extractfile(m).read())==expected[m.name]
 assert h(t.extractfile('installation_mapping_v1.json').read())==MAPSHA
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS',members=13)))
''',dict(HOST=I['hostname'],ARCHIVE=AR,SIZE=archive.stat().st_size,DIGEST=sha(archive),MAPSHA=sha(mapping)))
hash_code='''from pathlib import Path
import socket,hashlib,json
assert socket.gethostname()==HOST
total=0
for r in ROWS:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'];before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b);total+=len(b)
 after=p.stat();assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert h.hexdigest()==r['sha256'],str(p)
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS',files=len(ROWS),hashed_bytes=total)))
'''
rows=q['reused_readonly_bindings']
for i in range(0,len(rows),4):add('asset_'+str(i),hash_code,dict(HOST=I['hostname'],ROWS=rows[i:i+4]))
add('exclusive_install','''from pathlib import Path
import socket,hashlib,tarfile,os,json
assert socket.gethostname()==HOST and os.getuid()==1000
root=Path(ROOT);out=Path(OUT);archive=Path(ARCHIVE)
for p in [root,out]:assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
assert root.parent.is_dir() and out.parent.is_dir() and hashlib.sha256(archive.read_bytes()).hexdigest()==DIGEST
with tarfile.open(archive) as t:
 b=t.extractfile('installation_mapping_v1.json').read();assert hashlib.sha256(b).hexdigest()==MAPSHA
 rows=json.loads(b)['files'];assert len(rows)==12
 for r in rows:
  p=Path(r['target']);assert p.parent==root and not p.exists() and not p.is_symlink()
  b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 root.mkdir(mode=448)
 for r in rows:
  p=Path(r['target']);b=t.extractfile(r['member']).read()
  with p.open('xb') as f:f.write(b)
  assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
 (root/'control').mkdir(mode=448)
print(json.dumps(dict(status='TWELVE_FILES_EXCLUSIVE_INSTALL_PASS',files=12)))
''',dict(HOST=I['hostname'],ROOT=C,OUT=q['output'],ARCHIVE=AR,DIGEST=sha(archive),MAPSHA=sha(mapping)))
for i,(path,data) in enumerate(controls):
    add('control_'+str(i),'''from pathlib import Path
import socket,base64,zlib,hashlib,json
assert socket.gethostname()==HOST
p=Path(TARGET);assert p.parent.is_dir() and not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
b=zlib.decompress(base64.b64decode(DATA));assert hashlib.sha256(b).hexdigest()==DIGEST
with p.open('xb') as f:f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest()==DIGEST
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS',bytes=len(b))))
''',dict(HOST=I['hostname'],TARGET=path,DATA=base64.b64encode(zlib.compress(data,9)).decode(),DIGEST=hashlib.sha256(data).hexdigest()))
add('installed_authorize','''from pathlib import Path
import socket,hashlib,json,importlib.util
assert socket.gethostname()==HOST
p=Path(ENTRY);assert hashlib.sha256(p.read_bytes()).hexdigest()==ENTRYSHA
s=importlib.util.spec_from_file_location('rf_installed_contract_only',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def bound(path,digest):
 p=Path(path);assert hashlib.sha256(p.read_bytes()).hexdigest()==digest;return json.loads(p.read_bytes())
q=bound(REQUEST,REQUESTSHA);m.authorize(q,REQUESTSHA,bound(AUTH,AUTHSHA),AUTHSHA,bound(RUNTIME,RUNTIMESHA))
assert q['science']['full_forward']==5 and q['science']['full_loss']==q['science']['full_backward']==4
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS',model_calls=0)))
''',dict(HOST=I['hostname'],ENTRY=q['entry']['path'],ENTRYSHA=q['entry']['sha256'],REQUEST=L['request_path'],REQUESTSHA=RH,AUTH=L['authorization_path'],AUTHSHA=ah,RUNTIME=L['runtime_path'],RUNTIMESHA=rhash))
for i in range(0,len(mp['files']),4):
    rr=[dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']) for r in mp['files'][i:i+4]]
    add('prelaunch_installed_'+str(i),hash_code,dict(HOST=I['hostname'],ROWS=rr))
add('single_launch','''from pathlib import Path
import socket,os,subprocess,shutil,json,hashlib
assert socket.gethostname()==HOST and os.getuid()==1000
out=Path(OUT);claim=Path(CLAIM)
for p in [out,claim]:assert not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
assert subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
a=[x.strip() for x in subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
assert a[:4]==GPU and int(a[4])<=256 and shutil.disk_usage(out.parent).free>=4294967296
for path,h in CONTROLS:
 p=Path(path);assert not any(x.is_symlink() for x in (p,*p.parents)) and hashlib.sha256(p.read_bytes()).hexdigest()==h
with claim.open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=REQUESTSHA),f)
r=subprocess.run(['tmux','new-session','-d','-s',SESSION,'bash '+LAUNCHER]);assert r.returncode==0
print(json.dumps(dict(status='SINGLE_RF_CUDA_TMUX_SUBMITTED',session=SESSION,GPU=a)))
''',dict(HOST=I['hostname'],OUT=q['output'],CLAIM=L['launch_attempt_path'],SESSION=L['tmux_session'],GPU=[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])],CONTROLS=[(p,hashlib.sha256(b).hexdigest()) for p,b in controls],REQUESTSHA=RH,LAUNCHER=shlex.quote(L['launcher_path'])))

if '--static' in sys.argv:
    S=B/'authorized_execution_static_v1';S.mkdir()
    for label,code,command,seconds in scripts:
        with (S/(label+'.remote.py')).open('x',encoding='utf-8',newline='\n') as f:f.write(code)
    save(S/'review_v1.json',dict(status='ALL_REMOTE_COMMANDS_STATIC_PASS',controller_sha256=sha(Path(__file__)),request_sha256=RH,
         commands=len(scripts),max_command_bytes=max(len(x[2].encode()) for x in scripts),server_calls=0,control_files_materialized=False))
    print(json.dumps(dict(status='ALL_REMOTE_COMMANDS_STATIC_PASS',commands=len(scripts),max_bytes=max(len(x[2].encode()) for x in scripts))))
else:
    assert read(B/'authorized_execution_static_v1/review_v1.json')['controller_sha256']==sha(Path(__file__))
    O.mkdir();stage='before_first_call'
    try:
        for label,code,command,seconds in scripts:
            stage=label
            if label=='control_0':
                for name,data in [('authorization_v1.json',ab),('runtime_v1.json',rb),('launch_once_v1.sh',lb)]:
                    with (O/name).open('xb') as f:f.write(data)
            process=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(seconds),'--',command],capture_output=True,timeout=seconds+15)
            for kind,data in [('stdout',process.stdout),('stderr',process.stderr)]:
                with (O/(label+'_'+kind+'.bin')).open('xb') as f:f.write(data)
            assert process.returncode==0,(label,process.returncode,process.stdout.decode(errors='replace')[-1600:])
            result=json.loads(process.stdout);save(O/(label+'.json'),result)
            print(json.dumps(dict(stage=label,status=result['status'])),flush=True)
        save(O/'launch_receipt_v1.json',dict(status='SINGLE_RF_CUDA_ATTEMPT_SUBMITTED',request_sha256=RH,output=q['output'],tmux=L['tmux_session'],forwards=5,losses=4,backwards=4,optimizer_steps=0,automatic_retry=False))
    except BaseException as exc:
        save(O/'stop_receipt_v1.json',dict(status='STOPPED_NO_AUTOMATIC_RETRY',stage=stage,error=repr(exc),request_sha256=RH));raise
