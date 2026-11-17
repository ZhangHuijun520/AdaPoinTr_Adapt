import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz', 'bytes': 20390, 'sha256': 'c5993b324c3fcd735bdcd64df1c4ccadfa36de97476a7326dc3788eac15cc3c3'}, {'path': '/home/jovyan/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz.sha256', 'bytes': 118, 'sha256': '3d748409be604b46ff0865baa50b16eabe9b1e9d0cc47aaaffd7e65318d858cf'}, {'path': '/home/jovyan/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz.bytes', 'bytes': 7, 'sha256': 'e396522836f03f45b499a0064fd92c5f5209d8b48d8a86021fe61f5a3892cb19'}, {'path': '/home/jovyan/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz.contents.sha256', 'bytes': 1149, 'sha256': 'bcf43026f25c854409f4ba68f41c04edc20798f6719e0624efa94cef0ea336d3'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
