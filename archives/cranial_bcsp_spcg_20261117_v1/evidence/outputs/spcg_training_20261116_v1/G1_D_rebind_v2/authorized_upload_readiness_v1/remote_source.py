import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz', 'bytes': 21206, 'sha256': '65a0b9e0a9295e88eb76768e7dadf58476a582c0bac6365a0823093cebeb0ebb'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz.sha256', 'bytes': 118, 'sha256': '32de993bb8d0e509d05d2ab91a83866d054748a90acfdf3563797aae0e6b3cfb'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz.bytes', 'bytes': 7, 'sha256': 'ba10e35f56e3666dd5237a3a3a7c30a4182644ed95a40a48a21493c8c432fba6'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz.contents.sha256', 'bytes': 1136, 'sha256': '57c716a6debdca156c08fbee9ba04c9fdc48ff54604cd62fb5f435a9a797b925'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
