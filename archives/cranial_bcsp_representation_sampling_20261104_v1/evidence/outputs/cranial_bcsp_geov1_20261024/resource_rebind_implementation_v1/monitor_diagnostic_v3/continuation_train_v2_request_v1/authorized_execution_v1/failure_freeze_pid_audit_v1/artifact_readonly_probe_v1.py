import os,socket,json,stat,hashlib,base64,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v2')
assert all(stat.S_ISDIR(x.lstat().st_mode) for x in (r,*r.parents))
rows=[];dirs=[];total=0
def scan(p):
 global total
 for x in sorted(p.iterdir()):
  assert time.monotonic()-s<30 and len(rows)+len(dirs)<32
  st=x.lstat();mode=stat.S_IMODE(st.st_mode)
  if stat.S_ISDIR(st.st_mode):dirs.append(str(x));scan(x);continue
  assert stat.S_ISREG(st.st_mode),'linked/special: '+str(x)
  assert total+st.st_size<=8388608
  with x.open('rb') as f:data=f.read()
  end=x.stat();assert (st.st_ino,st.st_size,st.st_mtime_ns)==(end.st_ino,end.st_size,end.st_mtime_ns)
  total+=len(data);row=dict(path=str(x),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),mode=mode,uid=st.st_uid,mtime_ns=st.st_mtime_ns)
  if len(data)<=65536 and x.suffix not in ('.pth','.pt','.npz'):row['content_base64']=base64.b64encode(data).decode()
  rows.append(row)
scan(r)
print(json.dumps(dict(hostname=socket.gethostname(),uid=1000,files=rows,directories=dirs,total_bytes=total,seconds=time.monotonic()-s,server_writes=0)))
