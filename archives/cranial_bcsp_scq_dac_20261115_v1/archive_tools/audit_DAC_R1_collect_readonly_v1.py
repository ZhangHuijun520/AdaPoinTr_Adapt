"""One bounded formal readonly evidence collection; no remote files/ML imports/forward."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,sys,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1';F=B/'post_diagnostic_freeze_v1'
RH='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8';qp=B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json';assert hashlib.sha256(qp.read_bytes()).hexdigest()==RH
q=json.loads(qp.read_bytes());ROOT=q['entry']['path'].rsplit('/',1)[0]
prefix="""from pathlib import Path
import os,socket,json,hashlib,time,subprocess,base64
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
I=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1')
Q=I/'SCQ_DAC_R1_execution_request_v1.json'
assert hashlib.sha256(Q.read_bytes()).hexdigest()=='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'
q=json.loads(Q.read_bytes());O=Path(q['output']);T=time.monotonic()
assert not any(p.is_symlink() for root in (I,O) for p in (root,*root.parents))
def h(p):
 a=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):assert time.monotonic()-T<55;a.update(b)
 return a.hexdigest()
"""
inventory=prefix+"""
assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=int((O/'worker.pid').read_text())
try:assert q['entry']['path'].encode() not in (Path('/proc')/str(pid)/'cmdline').read_bytes()
except FileNotFoundError:pass
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
result={};total=0
for root,label in ((I,'installed'),(O,'output')):
 files={};dirs=[]
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n);continue
  s=p.stat();total+=s.st_size;assert len(files)<64 and total<1200000000
  d=h(p);a=p.stat();fp=lambda t:[t.st_dev,t.st_ino,t.st_mode,t.st_size,t.st_mtime_ns,t.st_ctime_ns]
  assert fp(s)==fp(a);files[n]=dict(bytes=s.st_size,sha256=d,fingerprint=fp(a))
 result[label]=dict(files=files,directories=dirs)
print(json.dumps(dict(status='FINISHED_EXACT_SCOPED_STABLE_INVENTORY',results=result,hashed_bytes=total,seconds=time.monotonic()-T,server_writes=0)))
"""
metadata=prefix+"""
files={};total=0
for root,label in ((I,'installed'),(O,'output')):
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.suffix in ('.pth','.npz','.gz'):continue
  assert not p.is_symlink() and p.stat().st_size<2097152
  raw=p.read_bytes();total+=len(raw);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
print(json.dumps(dict(status='CONTROL_AND_RUNTIME_METADATA_READONLY',files=files,bytes=total,server_writes=0)))
"""
archive=prefix+"""
import tarfile
c=json.loads((O/'completion.json').read_bytes());a=c['archive'];p=Path(a['path']);assert p.parent==O and p.stat().st_size==a['bytes'] and h(p)==a['sha256']
rows={r['name']:r for r in a['members']};assert len(rows)==len(a['members'])==24
assert (O/(p.name+'.sha256')).read_text().split()[0]==a['sha256'] and int((O/(p.name+'.bytes')).read_text())==a['bytes']
catalog={n:d for d,n in (l.split('  ',1) for l in (O/(p.name+'.contents.sha256')).read_text().splitlines())};assert len(catalog)==24
assert catalog=={n:r['sha256'] for n,r in rows.items()}
seen={};notes=[]
with tarfile.open(p,'r|gz') as t:
 for m in t:
  assert m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts and m.name not in seen and m.name in rows
  raw=t.extractfile(m).read();r=rows[m.name];assert len(raw)==m.size==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
  current=(O/m.name).read_bytes()
  if m.name=='resources.jsonl':
   assert current.startswith(raw);extra=current[len(raw):].splitlines();assert len(extra)==1 and json.loads(extra[0])['phase']=='archived'
   notes.append('archive resources is exact stable prefix; final archived sample added after packing by frozen entry')
  else:assert current==raw
  seen[m.name]=r
print(json.dumps(dict(status='ARCHIVE24_STREAM_MEMBERS_AND_SIDECARS_PASS',archive=dict(path=str(p),bytes=p.stat().st_size,sha256=a['sha256']),members=seen,notes=notes,server_writes=0)))
"""
scripts=[]
for label,src in [('inventory_before',inventory),('metadata',metadata),('archive',archive),('inventory_after',inventory)]:
 ast.parse(src,feature_version=(3,8));blob=base64.b85encode(zlib.compress(src.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048,(label,len(cmd.encode()))
 scripts.append((label,src,cmd))
if sys.argv[1:]!=['--execute']:
 F.mkdir()
 for label,src,cmd in scripts:
  with (F/(label+'_readonly_source.py')).open('x',encoding='utf-8') as f:f.write(src)
 with (F/'frozen_audit_scope_v1.json').open('x') as f:json.dump(dict(status='FROZEN_BEFORE_READONLY_AUDIT',controller_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),request_sha256=RH,calls=[dict(phase=l,command_bytes=len(cmd.encode()),timeout_seconds=60) for l,_,cmd in scripts],max_files_per_root=64,max_combined_hash_bytes_per_inventory=1200000000,metadata_limit=16777216,server_writes=0,model_imports=0,new_forward=0),f,indent=2)
 print('AUDIT_SCOPE_STATIC_PASS_NO_CONNECTION')
else:
 assert json.loads((F/'frozen_audit_scope_v1.json').read_bytes())['controller_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 answers={};phase='not_started'
 try:
  with (F/'readonly_audit_claim_v1.json').open('x') as f:json.dump(dict(one_readonly_batch=True,request_sha256=RH),f)
  for label,src,cmd in scripts:
   phase=label;print(label,flush=True)
   x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',cmd],capture_output=True,timeout=75)
   for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
    with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
   assert x.returncode==0,(label,x.returncode,x.stdout.decode(errors='replace')[-1500:])
   v=json.loads(x.stdout);answers[label]=v
   with (F/(label+'_result_v1.json')).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
   if label=='metadata':
    for name,r in v['files'].items():
     raw=base64.b64decode(r['base64']);assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
     p=F/'downloads'/name;p.parent.mkdir(parents=True,exist_ok=True)
     with p.open('xb') as f:f.write(raw)
  assert answers['inventory_before']['results']==answers['inventory_after']['results'],'audit-time content drift'
  a=answers['archive']['archive'];local=F/'downloads'/Path(a['path']).name
  phase='download_verified_archive'
  x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',a['path'],'/mnt/e/'+local.absolute().as_posix()[3:],'--timeout','60'],capture_output=True,timeout=75)
  for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
   with (F/(phase+'_'+k+'.bin')).open('xb') as f:f.write(b)
  assert x.returncode==0 and local.stat().st_size==a['bytes'] and hashlib.sha256(local.read_bytes()).hexdigest()==a['sha256']
  with (F/'collection_complete_v1.json').open('x') as f:json.dump(dict(status='FORMAL_READONLY_EVIDENCE_COLLECTION_COMPLETE',request_sha256=RH,remote_inventory_stable=True,archive_download_verified=True,server_writes=0,new_forward=0),f,indent=2)
  print(json.dumps(dict(status='READONLY_COLLECTION_AND_ARCHIVE_DOWNLOAD_PASS',archive_bytes=a['bytes'])))
 except BaseException as exc:
  with (F/'collection_failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc)),f,ensure_ascii=False,indent=2)
  raise
