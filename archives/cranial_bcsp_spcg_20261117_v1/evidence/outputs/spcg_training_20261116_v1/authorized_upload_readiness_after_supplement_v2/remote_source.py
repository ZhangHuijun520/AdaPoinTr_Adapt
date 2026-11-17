import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz', 'bytes': 17906, 'sha256': '1e06b11d9c4d297f999dc64b0678174b16030f1c96dad57717cca351151c7462'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz.sha256', 'bytes': 118, 'sha256': 'bdd22921a068aa7732a396771b8f8c3a81d8fa69dfe68f54a9a2d2621d8c9ec5'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz.bytes', 'bytes': 7, 'sha256': '2bd192259c37ca9ac4085717a80138be10b88274be767d0f270fc5e63a26b44e'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz.contents.sha256', 'bytes': 1028, 'sha256': '04a5c8fcae19b34f2f3005d60522120603211f46772e3be49da641680c07b53f'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
