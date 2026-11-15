"""Bounded formal readonly collector. No model imports, writes or inference remotely."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_capture_implementation_20261114_v1/pending_request_v1'
F=R/'outputs/scq_rf_audit_20261114_v1';F.mkdir()
Q=B/'payload/SCQ_RF_ten_memory_execution_request_v1.json'
QH='51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'
assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH;q=json.loads(Q.read_bytes())
prefix="""from pathlib import Path,PurePosixPath
import socket,os,subprocess,json,hashlib,time,sys
assert socket.gethostname()==HOST and os.getuid()==1000
O=Path(OUT);I=Path(INSTALL)
assert not any(p.is_symlink() for p in (O,*O.parents,I,*I.parents))
qp=I/'SCQ_RF_ten_memory_execution_request_v1.json';assert hashlib.sha256(qp.read_bytes()).hexdigest()==QHASH
q=json.loads(qp.read_bytes())
"""
values=dict(HOST=q['identity']['hostname'],OUT=q['output'],INSTALL=q['entry']['path'].rsplit('/',1)[0],QHASH=QH)
class Bind(ast.NodeTransformer):
 def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
prefix=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(prefix))))+'\n'
sources={}
sources['finished']='''assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=(O/'worker.pid').read_text().strip();p=Path('/proc/'+pid)
assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip();a=[x.strip() for x in gpu.split(',')];I=q['identity'];assert a==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='EXIT0_TMUX_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),GPU=a,free_disk_bytes=__import__('shutil').disk_usage(O).free)))
'''
inventory='''def inventory(root):
 files={};dirs=[];total=0
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n);continue
  b=p.stat();total+=b.st_size;assert len(files)<600 and b.st_size<1073741824 and total<2147483648
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  a=p.stat();fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
  assert fp(b)==fp(a)
  files[n]=dict(bytes=a.st_size,sha256=h.hexdigest(),fingerprint=fp(a))
 return dict(files=files,directories=dirs,hashed_bytes=total)
print(json.dumps(dict(status='EXACT_INVENTORY_AND_STABLE_HASHES',output=inventory(O),installed=inventory(I))))
'''
sources['inventory_before']=inventory
sources['metadata']='''import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or (root==O and p.suffix in ('.gz','.npz')):continue
  assert not p.is_symlink() and p.stat().st_size<8388608
  b=p.read_bytes();total+=len(b);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READ',files=files,bytes=total)))
'''
sources['archive']='''import tarfile
c=json.loads((O/'completion.json').read_bytes());rs={r['name']:r for r in c['archive']['members']}
assert len(rs)==len(c['archive']['members'])==15
with tarfile.open(O/'development_predictions_v1.tar.gz') as t:
 ms=t.getmembers();assert len(ms)==15 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<8388608
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
print(json.dumps(dict(status='ALL15_ARCHIVE_MEMBER_BYTES_MATCH',members=15,server_extractions=0)))
'''
sources['inventory_after']=inventory
scripts=[]
def add(label,code):
 ast.parse(code,feature_version=(3,8));compile(code,label,'exec');b=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(b)+')))']);assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 scripts.append((label,code,cmd))
for name in ['finished','inventory_before','metadata']:add(name,prefix+sources[name])
static=B/'preexecution_static_v1'
for p in [*sorted(static.glob('asset_*.remote.py')),*sorted(static.glob('checkpoint_*.remote.py')),static/'inputs10.remote.py']:add('fresh_'+p.stem,p.read_text(encoding='utf-8'))
for name in ['archive','inventory_after']:add(name,prefix+sources[name])
def save(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
save('bounded_scope_v1.json',dict(status='READONLY_FORMAL_AUDIT_SCOPE',request_sha256=QH,scripts=len(scripts),max_command_bytes=max(len(v[2].encode()) for v in scripts),expected_captures=10,expected_output_files=23,expected_installed_files=21,server_writes=0,new_forward=0,checkpoint_loads=0))
stage='begin'
try:
 for label,code,cmd in scripts:
  stage=label
  with (F/(label+'.remote.py')).open('x',encoding='utf-8') as f:f.write(code)
  x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',cmd],capture_output=True,timeout=75)
  for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
   with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
  assert x.returncode==0,(label,x.stdout.decode(errors='replace')[-1800:]);v=json.loads(x.stdout);save(label+'_result_v1.json',v)
  if label=='metadata':
   for name,r in v['files'].items():
    p=F/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(r['base64']);assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
    with p.open('xb') as f:f.write(b)
  print(json.dumps(dict(stage=label,status=v['status'])),flush=True)
 save('collection_complete_v1.json',dict(status='READONLY_COLLECTION_COMPLETE',stages=len(scripts),request_sha256=QH,server_writes=0,new_forward=0))
except BaseException as exc:
 save('collection_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',stage=stage,error=repr(exc)));raise
