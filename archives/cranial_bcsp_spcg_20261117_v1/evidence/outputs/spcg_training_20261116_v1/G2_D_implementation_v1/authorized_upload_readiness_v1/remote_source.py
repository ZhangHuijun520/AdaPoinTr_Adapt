import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz', 'bytes': 22774, 'sha256': 'a9809c831ab1fa3aba196d533f1e80057ed4b3be505f7c32e0a1986e200c8f48'}, {'path': '/home/jovyan/bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz.sha256', 'bytes': 118, 'sha256': '49dd33296d028e636f827335337ac9e480fa1e84ea4b97f6be4f13fc92116e41'}, {'path': '/home/jovyan/bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz.bytes', 'bytes': 7, 'sha256': 'be8785e4f1ec6065365a35ac36e8bc8794878c7ef10c9b834bae61e144115e1e'}, {'path': '/home/jovyan/bcsp_spcg_G2_D_training_pending_20261117_v1.tar.gz.contents.sha256', 'bytes': 1253, 'sha256': '41dfc910759bbef5c65e6295fb888dc53ac33b5532be65d7cf91e8d5a3d38798'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
