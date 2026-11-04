import os,socket,json,hashlib,stat,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
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
m=Path('/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.installation_map.json')
assert not m.is_symlink() and m.stat().st_size<65536;raw=m.read_bytes();assert hashlib.sha256(raw).hexdigest()=='93d5ca2e34ddf39a5ecc40e53d8610b1c05d35ba1ead5082f28947f6119f6332'
q=json.loads(raw);assert len(q['installation_map'])==10
for r in q['installation_map']:
 assert time.monotonic()-s<45
 p=Path(r['server_target']);assert R in p.parents
 try:rows.append(inspect(p))
 except Exception as e:rows.append(dict(path=str(p),status='BLOCKED',error=str(e)));break
print(json.dumps(dict(rows=rows,missing_parents=sorted(missing),hashed_bytes=total,seconds=time.monotonic()-s,server_writes=0)))
