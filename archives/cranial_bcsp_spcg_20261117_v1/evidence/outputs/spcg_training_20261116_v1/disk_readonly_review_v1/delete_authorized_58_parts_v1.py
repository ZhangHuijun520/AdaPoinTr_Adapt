"""One exact-scope deletion of duplicate parts; retain full weights and all other files."""
from pathlib import Path
import hashlib,json,base64,zlib,subprocess
V=Path(__file__).resolve().parent;O=V/'authorized_delete58_v1';O.mkdir()
scope=V/'candidate_duplicate_parts_scope_v1.json';assert hashlib.sha256(scope.read_bytes()).hexdigest()=='d9466d6ad42a50acada571d1ebd02c38e1fc0eb50675b62e0bb36a3862f35ec4';d=json.loads(scope.read_bytes())
rows=[{k:x[k] for k in ['path','bytes','sha256']} for x in d['files']]
canonical=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert len(rows)==58 and sum(x['bytes'] for x in rows)==957620838
code="""from pathlib import Path
import os,socket,json,hashlib,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1');rows=[];states={};start=time.monotonic()
retained=RETAINED
def meta(p):
 assert p.is_absolute() and p.is_relative_to(r) and not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_nlink==1;return (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)
before=os.statvfs(r);before=before.f_bavail*before.f_frsize
for fold,wrec in zip(['C','D'],retained):
 w=Path(wrec['path']);wm=meta(w);assert wm[0]==wrec['bytes'];whole=hashlib.sha256()
 with w.open('rb') as f:
  for i in range(29):
   assert time.monotonic()-start<40;p=r/('parts_restore_v3_'+fold)/('part_%03d.bin'%i);pm=meta(p);b=p.read_bytes();assert len(b)==pm[0] and b==f.read(len(b));whole.update(b);assert meta(p)==pm;states[p]=pm;rows.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  assert f.read(1)==b''
 assert meta(w)==wm and whole.hexdigest()==wrec['sha256'];states[w]=wm
assert hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='CANONICAL'
assert all(meta(p)==v for p,v in states.items())
print(json.dumps(dict(phase='ALL58_HASHES_AND_RETAINED_WEIGHTS_PASS',files=58)),flush=True)
deleted=[]
for row in rows:
 p=Path(row['path']);assert meta(p)==states[p];p.unlink();deleted.append(str(p));print(json.dumps(dict(deleted=str(p))),flush=True)
assert all(not Path(p).exists() for p in deleted) and all(meta(Path(x['path']))==states[Path(x['path'])] for x in retained)
after=os.statvfs(r);after=after.f_bavail*after.f_frsize
print(json.dumps(dict(status='DELETED_EXACT58_RETAINED_WEIGHTS_UNCHANGED',deleted_count=len(deleted),deleted_bytes=sum(x['bytes'] for x in rows),retained=retained,available_before_bytes=before,available_after_bytes=after,minimum_free_bytes=int(8.5*1024**3),meets_original_threshold=after>=int(8.5*1024**3),training_started=False)),flush=True)
""".replace('RETAINED',repr(d['retained']),1).replace('CANONICAL',canonical(rows))
compile(code,'delete58','exec');(O/'remote_source.py').write_text(code,encoding='utf-8')
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--','/usr/bin/python3','-I','-S','-B','-c',c]
n=len(subprocess.list2cmdline(args).encode());assert n<=2048,n
(O/'static_review.json').write_text(json.dumps(dict(scope_sha256=hashlib.sha256(scope.read_bytes()).hexdigest(),rows_digest=canonical(rows),command_bytes=n,all_remote_compiled=True)),encoding='utf-8')
p=subprocess.run(args,capture_output=True,timeout=55);(O/'stdout.bin').write_bytes(p.stdout);(O/'stderr.bin').write_bytes(p.stderr);(O/'exit.json').write_text(json.dumps(dict(returncode=p.returncode)),encoding='utf-8');assert p.returncode==0,('STOP_NO_RETRY',p.returncode)
events=[json.loads(x) for x in p.stdout.splitlines()];assert events[-1]['deleted_count']==58
(O/'result.json').write_text(json.dumps(events[-1],ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(events[-1]))
