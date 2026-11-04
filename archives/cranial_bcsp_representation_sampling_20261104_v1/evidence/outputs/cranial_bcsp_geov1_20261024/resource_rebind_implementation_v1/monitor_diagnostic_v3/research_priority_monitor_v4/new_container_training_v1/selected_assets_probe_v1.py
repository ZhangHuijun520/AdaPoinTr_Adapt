import os,socket,json,hashlib,stat,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
c=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1')
def read(p,size,digest):
 for a in p.parents:assert stat.S_ISDIR(a.lstat().st_mode),'linked parent'
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size==size
 raw=p.read_bytes();end=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino)
 assert hashlib.sha256(raw).hexdigest()==digest;return raw
r=json.loads(read(c/'readonly_identity_assets_upload_report_v1.json',22014,'1ccb8c7fc712cdecb04f260d84b827e422fb1d6926110664783f0033ef9a33c6'))
rows=[];total=0
for x in r['frozen_assets']['manifest']:
 p=Path(x['path']);size=x['expected_bytes'];digest=x['expected_sha256'];assert size<=20000000
 read(p,size,digest);total+=size;assert total<=20000000 and time.monotonic()-s<30
 rows.append(dict(path=str(p),bytes=size,sha256=digest))

assert len(rows)==30
print(json.dumps(dict(status='SELECTED30_HASH_PASS',assets=rows,hashed_bytes=total,server_writes=0,seconds=time.monotonic()-s)))
