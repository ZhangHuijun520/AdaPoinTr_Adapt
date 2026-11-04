import os,socket,json,stat,hashlib,base64,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1')
paths=list((r/'control').iterdir())+[r/x for x in ['bcsp_training_entry_v2.py','bcsp_training_contract_v2.py','bcsp_training_runtime_v5.py','static_training_config_v1.json']]
assert len(paths)==11
rows=[]
for p in sorted(paths):
 assert time.monotonic()-s<20
 for a in p.parents:assert stat.S_ISDIR(a.lstat().st_mode),'linked parent'
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<65536
 raw=p.read_bytes();t=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino)
 rows.append(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),mode=stat.S_IMODE(st.st_mode),uid=st.st_uid,content_base64=base64.b64encode(raw).decode() if p.name=='launch_attempt_v1.json' else None))
print(json.dumps(dict(files=rows,seconds=time.monotonic()-s,server_writes=0)))
