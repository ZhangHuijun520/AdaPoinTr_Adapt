from pathlib import Path
import json,hashlib,os,socket,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1');rows=[];retained=[];start=time.monotonic()
def meta(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_nlink==1;return (s.st_size,s.st_mtime_ns,s.st_ino)
for fold in ['C','D']:
 w=r/'weights_restored_v3'/('LQI_'+fold+'_epoch99_step3900.pth');wm=meta(w);parts=sorted((r/('parts_restore_v3_'+fold)).glob('part_*.bin'));assert [x.name for x in parts]==['part_%03d.bin'%i for i in range(29)];whole=hashlib.sha256()
 with w.open('rb') as f:
  for p in parts:
   assert time.monotonic()-start<40;pm=meta(p);b=p.read_bytes();assert b==f.read(len(b)) and len(b)==pm[0];whole.update(b);assert meta(p)==pm;rows.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),retained_full_copy=str(w),segment_equal=True))
  assert f.read(1)==b''
 assert meta(w)==wm;retained.append(dict(path=str(w),bytes=wm[0],sha256=whole.hexdigest()))
print(json.dumps(dict(status='58_PARTS_EXACT_DUPLICATES_OF_RETAINED_FULL_WEIGHTS',files=rows,retained=retained,bytes=sum(x['bytes'] for x in rows))))
