from pathlib import Path
import socket, os, subprocess, hashlib, json, time
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
assert hashlib.sha256((I / 'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes()).hexdigest() == '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
q = json.loads((I / 'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes())
files={};directories={};total=0
related=[q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],next(r for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py')]
paths=[]
for root,label in [(O,'output'),(I,'installed')]:
 dirs=['.']
 for p in root.rglob('*'):
  assert not p.is_symlink() and (p.is_dir() or p.is_file()),str(p)
  if p.is_dir():dirs.append(str(p.relative_to(root)));assert len(dirs)<=16
  else:paths.append((label+'/'+str(p.relative_to(root)),p));assert len(paths)<=32
 directories[label]=sorted(dirs)
for i,r in enumerate(related):paths.append(('related/'+str(i)+'_'+Path(r['path']).name,Path(r['path'])))
archive=Path('/home/jovyan/bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz')
for suffix in ['', '.sha256','.bytes','.contents.sha256']:paths.append(('upload/'+archive.name+suffix,Path(str(archive)+suffix)))
assert len(paths)<=32
fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for name,p in paths:
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 before=p.stat();total+=before.st_size;assert total<=8388608 and before.st_size<=2097152
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 after=p.stat();assert fp(before)==fp(after)
 files[name]=dict(path=str(p),bytes=after.st_size,sha256=h.hexdigest(),fingerprint=fp(after))
print(json.dumps(dict(status='BOUNDED_STABLE_FAILURE_INVENTORY',files=files,directories=directories,hashed_bytes=total)))
