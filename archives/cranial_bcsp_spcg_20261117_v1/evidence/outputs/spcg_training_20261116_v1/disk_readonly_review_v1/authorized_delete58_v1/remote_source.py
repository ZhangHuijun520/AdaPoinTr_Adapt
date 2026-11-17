from pathlib import Path
import os,socket,json,hashlib,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1');rows=[];states={};start=time.monotonic()
retained=[{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/weights_restored_v3/LQI_C_epoch99_step3900.pth', 'bytes': 478810419, 'sha256': 'd8d819ffb9ed1f931c60f0ee96e9ae9c4093d61c73c2152a52f13b8cd95a0ddf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/weights_restored_v3/LQI_D_epoch99_step3900.pth', 'bytes': 478810419, 'sha256': '2afd1b4540b856d4c829786729d8c2df80943edd65a0f01af412940fd973e5ed'}]
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
assert hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='a88a5d064431f34d07af6c96c9a89c5a3dd063eb900f5fae4dcbd16503f4b2f1'
assert all(meta(p)==v for p,v in states.items())
print(json.dumps(dict(phase='ALL58_HASHES_AND_RETAINED_WEIGHTS_PASS',files=58)),flush=True)
deleted=[]
for row in rows:
 p=Path(row['path']);assert meta(p)==states[p];p.unlink();deleted.append(str(p));print(json.dumps(dict(deleted=str(p))),flush=True)
assert all(not Path(p).exists() for p in deleted) and all(meta(Path(x['path']))==states[Path(x['path'])] for x in retained)
after=os.statvfs(r);after=after.f_bavail*after.f_frsize
print(json.dumps(dict(status='DELETED_EXACT58_RETAINED_WEIGHTS_UNCHANGED',deleted_count=len(deleted),deleted_bytes=sum(x['bytes'] for x in rows),retained=retained,available_before_bytes=before,available_after_bytes=after,minimum_free_bytes=int(8.5*1024**3),meets_original_threshold=after>=int(8.5*1024**3),training_started=False)),flush=True)
