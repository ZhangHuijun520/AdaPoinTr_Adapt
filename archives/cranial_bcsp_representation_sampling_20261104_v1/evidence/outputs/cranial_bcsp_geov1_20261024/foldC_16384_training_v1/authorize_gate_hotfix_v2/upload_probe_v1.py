import os,socket,json,hashlib,stat
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
p=Path('/home/jovyan/bcsp_foldC_16384_authorize_hotfix_v2.tar.gz')
for a in p.parents:assert stat.S_ISDIR(a.lstat().st_mode)
s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size==11107
raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='977e2ff0c25af03b57d87ec208318befd12b6243a2c9f3ae359c483b722aff1f'
assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
c=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1')
rows=[]
for name in ['bcsp_training_entry_foldC_16384_v6.py','bcsp_training_contract_foldC_16384_v4.py']:
 t=c/name
 for a in t.parents:assert stat.S_ISDIR(a.lstat().st_mode)
 rows.append(dict(path=str(t),exists=os.path.lexists(t),parent_writable=os.access(t.parent,os.W_OK|os.X_OK)))
print(json.dumps(dict(status='UPLOAD_HASH_PASS',hostname=socket.gethostname(),upload=dict(path=str(p),bytes=len(raw),sha256=digest),targets=rows,server_writes=0,CUDA_calls=0,training_started=False)))
