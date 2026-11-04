import os,socket,json,hashlib,stat,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
R=Path('/home/jovyan/adapointr_work/PoinTr');assert all(stat.S_ISDIR(x.lstat().st_mode) for x in (R,*R.parents))
rows=[];missing=set();total=0
def inspect(p):
 global total
 for a in reversed(p.parents):
  if not os.path.lexists(a):missing.add(str(a));continue
  assert stat.S_ISDIR(a.lstat().st_mode),'parent not directory: '+str(a)
 if not os.path.lexists(p):return dict(path=str(p),status='ABSENT')
 st=p.lstat();assert stat.S_ISREG(st.st_mode),'target not regular: '+str(p)
 assert st.st_size<=4194304 and total+st.st_size<=67108864,'hash byte budget: '+str(p)
 raw=p.read_bytes();total+=len(raw)
 assert (st.st_size,st.st_mtime_ns,st.st_ino)==(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino),'changed: '+str(p)
 return dict(path=str(p),status='PRESENT',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
m=Path('/home/jovyan/bcsp_foldc_8192_train_inputs_v1.contents.sha256')
assert not m.is_symlink() and m.stat().st_size<65536;raw=m.read_bytes();assert hashlib.sha256(raw).hexdigest()=='1d5f43673c76b93d3195aad25e19de4a229fdc2c23505395d993c548175b823e'
lines=[x.split('  ',1) for x in raw.decode().splitlines()];assert len(lines)==327
for digest,name in lines:
 assert time.monotonic()-s<45
 p=R/('third_party/bcsp_geov1_training_foldc_8192_seed0_v1/'+name[5:] if name.startswith('code/') else 'data/bcsp_geov1_foldc_8192_seed0_v1/'+name[5:])
 try:rows.append(inspect(p))
 except Exception as e:rows.append(dict(path=str(p),status='BLOCKED',error=str(e)));break
print(json.dumps(dict(rows=rows,missing_parents=sorted(missing),hashed_bytes=total,seconds=time.monotonic()-s,server_writes=0)))
