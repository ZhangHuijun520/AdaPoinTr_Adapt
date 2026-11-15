"""Authorized exact28-file installation + one 20/40 diagnostic. Byte-preserving short calls."""
from pathlib import Path
import ast,base64,hashlib,importlib.util,json,shlex,subprocess,sys,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1'
O=B/'authorized_execution_v1';S=B/'authorized_execution_static_v1'
RH='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
Q=B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def save(p,j):
 with p.open('xb') as f:f.write(jb(j))
assert sha(Q)==RH;q=read(Q);I=q['identity'];L=q['launch_contract']
root=q['deployment_contract']['new_parent_directory'];archive='/home/jovyan/scq_dac_r1_frozen20_transport_20261115_v1.tar.gz'
ARCHIVE_SHA='350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01'
manifest=R/'server_uploads/scq_dac_r1_frozen20_20261115_v1/install_manifest_v1.json';M=read(manifest)
assert M['request_sha256']==RH and len(M['files'])==28
entry_path=B/'bcsp_scq_dac_r1_entry_v1.py';assert sha(entry_path)==q['entry']['sha256']
sp=importlib.util.spec_from_file_location('DAC_authorized_launcher_render_only',entry_path);entry=importlib.util.module_from_spec(sp);sp.loader.exec_module(entry)
auth=dict(schema='bcsp-dac-r1-authorization-v1',request_sha256=RH,explicit_user_authorization=True,user_authorization_text='下一步单独明确授权以下完整SHA256，才可重验条件、不覆盖安装并执行唯一一次20次完整forward＋40次decoder-only、零更新诊断。上下文唯一完整SHA256：'+RH)
ab=jb(auth);ah=hashlib.sha256(ab).hexdigest();runtime=dict(schema='bcsp-dac-r1-runtime-v1',request_sha256=RH,authorization_sha256=ah);rb=jb(runtime);rhash=hashlib.sha256(rb).hexdigest();lb=entry.render_launcher(q,RH,ah,rhash).encode()
controls=[(L['authorization'],ab),(L['runtime'],rb),(L['launcher'],lb)]
scripts=[]
def add(label,code,values=None,seconds=60):
 if values:
  class Bind(ast.NodeTransformer):
   def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
  code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(code))))
 ast.parse(code,feature_version=(3,8));compile(code,label,'exec')
 blob=base64.b85encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))'])
 assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 scripts.append((label,code,cmd,seconds))
for label in ('identity_targets','target_absence','frozen_sources_provider','twenty_inputs'):
 add('fresh_'+label,(B/'server_readiness_v2'/(label+'_readonly_source.py')).read_text(encoding='utf-8'))
pins=read(R/'server_uploads/scq_dac_r1_frozen20_20261115_v1/transport_verification_receipt_v1.json')
add('fresh_uploaded_four_files','''from pathlib import Path
import hashlib,json,socket
assert socket.gethostname()==HOST
def h(p):
 a=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):a.update(b)
 return a.hexdigest()
for r in FILES:
 p=Path('/home/jovyan')/Path(r['path']).name
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and h(p)==r['sha256']
print(json.dumps(dict(status='FRESH_FOUR_UPLOAD_HASHES_PASS',files=4)))
''',dict(HOST=I['hostname'],FILES=[dict(path=Path(r['path']).name,bytes=r['bytes'],sha256=r['sha256']) for r in [pins['archive']]+pins['sidecars']]))
add('exclusive_install','''from pathlib import Path,PurePosixPath
import os,socket,json,tarfile,hashlib,time
assert socket.gethostname()==HOST and os.getuid()==1000
P=Path(PROJECT);root=Path(ROOT);out=Path(OUT);p=Path(ARCHIVE);T=time.monotonic()
def clean(x):
 x=Path(x);assert not any(y.is_symlink() for y in (x,*x.parents));return x
def stream(f):
 h=hashlib.sha256();n=0
 for b in iter(lambda:f.read(4194304),b''):
  n+=len(b);h.update(b);assert time.monotonic()-T<110
 return n,h.hexdigest()
assert P.resolve()==P and clean(root.parent).is_dir() and os.access(root.parent,os.W_OK|os.X_OK)
for x in (root,out):assert not clean(x).exists()
assert clean(p).stat().st_size==906620311
st=p.stat()
with p.open('rb') as f:assert stream(f)[1]==ARCHIVESHA
side=clean(str(p)+'.contents.sha256');assert side.is_file()
catalog={n:h for h,n in (line.split('  ',1) for line in side.read_text().splitlines())};assert len(catalog)==30
rows=None;seen=set()
with tarfile.open(p,'r|gz') as t:
 for m in t:
  assert m.isfile() and m.name in catalog and m.name not in seen and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts
  if m.name=='metadata/install_manifest_v1.json':
   b=t.extractfile(m).read();assert hashlib.sha256(b).hexdigest()==MAPSHA;v=json.loads(b);assert v['request_sha256']==RH and v['root']==str(root);rows=v['files'];a=(len(b),hashlib.sha256(b).hexdigest())
  else:
   with t.extractfile(m) as f:a=stream(f)
  assert a==(m.size,catalog[m.name]);seen.add(m.name)
assert len(seen)==30 and len(rows)==28 and len({r['target'] for r in rows})==28
for r in rows:
 target=clean(r['target']);assert str(target.relative_to(root))==r['member'][8:] and r['member'].startswith('payload/') and not target.exists()
assert (st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns)
os.umask(63);root.mkdir(mode=448)
for n in ('weights','replay','control'):(root/n).mkdir(mode=448)
written=[]
with tarfile.open(p,'r|gz') as t:
 bymember={r['member']:r for r in rows}
 for m in t:
  if m.name not in bymember:continue
  r=bymember[m.name];target=clean(r['target']);assert not target.exists()
  with t.extractfile(m) as source,target.open('xb') as dest:
   while True:
    b=source.read(4194304)
    if not b:break
    dest.write(b)
  with target.open('rb') as f:assert stream(f)==(r['bytes'],r['sha256'])
  written.append(r['target'])
assert len(written)==28
print(json.dumps(dict(status='EXACT28_EXCLUSIVE_INSTALL_HASH_PASS',files=28,root=str(root),seconds=time.monotonic()-T)))
''',dict(HOST=I['hostname'],PROJECT=I['project'],ROOT=root,OUT=q['output'],ARCHIVE=archive,ARCHIVESHA=ARCHIVE_SHA,CONTENTSHA=pins['sidecars'][2]['sha256'],MAPSHA=sha(manifest),RH=RH),120)
for i,(path,data) in enumerate(controls):
 add('materialize_control_'+str(i),'''from pathlib import Path
import socket,base64,zlib,hashlib,json
assert socket.gethostname()==HOST
p=Path(TARGET);assert p.parent.is_dir() and not p.exists() and not any(x.is_symlink() for x in (p,*p.parents))
b=zlib.decompress(base64.b85decode(DATA));assert hashlib.sha256(b).hexdigest()==SHA
with p.open('xb') as f:f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_MATERIALIZED',name=p.name,sha256=SHA)))
''',dict(HOST=I['hostname'],TARGET=path,DATA=base64.b85encode(zlib.compress(data,9)).decode(),SHA=hashlib.sha256(data).hexdigest()))
add('installed_authorize_contract','''from pathlib import Path
import importlib.util,json,hashlib,socket,sys
assert socket.gethostname()==HOST
p=Path(ENTRY);assert hashlib.sha256(p.read_bytes()).hexdigest()==ESHA
s=importlib.util.spec_from_file_location('dac_installed_authorize_only',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def record(path,h):return dict(path=path,bytes=Path(path).stat().st_size,sha256=h)
q=m.authorize(record(Q,RH),record(A,AH),record(R,RSHA))
assert q['calls']==dict(native=20,decoder_only=40,decoder=60,h1_new=20,h1_old=20,first_head=20)
assert not any(x in sys.modules for x in ('torch','numpy','models.AdaPoinTr'))
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_PATH_PASS_NO_MODEL_IMPORT',request_sha256=RH)))
''',dict(HOST=I['hostname'],ENTRY=q['entry']['path'],ESHA=q['entry']['sha256'],Q=L['request_path'],RH=RH,A=L['authorization'],AH=ah,R=L['runtime'],RSHA=rhash))
add('claim_and_single_tmux','''from pathlib import Path
import socket,json,hashlib,subprocess,shlex,os
assert socket.gethostname()==HOST and os.getuid()==1000
def valid(p,h):
 p=Path(p);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and hashlib.sha256(p.read_bytes()).hexdigest()==h
valid(Q,RH);valid(A,AH);valid(R,RSHA);valid(L,LSHA)
assert not Path(OUT).exists() and subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==1
m=Path(MARKER);assert not m.exists() and not any(x.is_symlink() for x in (m,*m.parents))
with m.open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=RH),f)
x=subprocess.run(['tmux','new-session','-d','-s',SESSION,shlex.join(['/bin/bash',L])],capture_output=True,text=True,timeout=10)
assert x.returncode==0,dict(rc=x.returncode,stdout=x.stdout,stderr=x.stderr)
print(json.dumps(dict(status='SINGLE_DAC_R1_TMUX_ATTEMPT_SUBMITTED',session=SESSION,request_sha256=RH,marker=str(m),automatic_retry=False)))
''',dict(HOST=I['hostname'],Q=L['request_path'],RH=RH,A=L['authorization'],AH=ah,R=L['runtime'],RSHA=rhash,L=L['launcher'],LSHA=hashlib.sha256(lb).hexdigest(),OUT=q['output'],SESSION=L['tmux_session'],MARKER=q['launch_attempt']))
if sys.argv[1:]!=['--execute']:
 S.mkdir()
 for label,code,cmd,seconds in scripts:
  with (S/(label+'.remote.py')).open('x',encoding='utf-8') as f:f.write(code)
 save(S/'static_review_v1.json',dict(status='ALL_SHORT_REMOTE_SCRIPTS_STATIC_PASS',controller_sha256=sha(Path(__file__)),request_sha256=RH,scripts=len(scripts),maximum_command_bytes=max(len(c.encode()) for _,_,c,_ in scripts),Python38_compatible_syntax=True,controls_not_materialized=True))
 print(json.dumps(dict(status='STATIC_PASS_NO_SERVER_CALLS',scripts=len(scripts),maximum_bytes=max(len(c.encode()) for _,_,c,_ in scripts))))
else:
 assert read(S/'static_review_v1.json')['controller_sha256']==sha(Path(__file__))
 O.mkdir();stage='before_first_call'
 try:
  for label,code,cmd,seconds in scripts:
   stage=label;print(label,flush=True)
   if label=='materialize_control_0':
    for name,data in [('authorization_v1.json',ab),('runtime_v1.json',rb),('launch_once_v1.sh',lb)]:
     with (O/name).open('xb') as f:f.write(data)
   x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(seconds),'--',cmd],capture_output=True,timeout=seconds+15)
   for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
    with (O/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
   assert x.returncode==0,(label,x.returncode,x.stdout.decode(errors='replace')[-2000:],x.stderr.decode(errors='replace')[-1000:])
   value=json.loads(x.stdout);save(O/(label+'.json'),value)
  save(O/'launch_receipt_v1.json',dict(status='SINGLE_DAC_R1_ATTEMPT_SUBMITTED_AWAITING_OBSERVATION',request_sha256=RH,output=q['output'],session=L['tmux_session'],native=20,decoder_only=40,optimizer_steps=0,automatic_retry=False))
 except BaseException as exc:
  save(O/'stop_receipt_v1.json',dict(status='FAILED_STOP_NO_RETRY',phase=stage,error=repr(exc),request_sha256=RH));raise
