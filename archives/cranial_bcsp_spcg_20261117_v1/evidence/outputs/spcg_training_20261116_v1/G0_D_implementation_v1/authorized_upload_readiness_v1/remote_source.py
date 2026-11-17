import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz', 'bytes': 20279, 'sha256': 'fa101a7488b5e928d0eddaea6e4b4d330b9ba45776552164ae1434e67e63df60'}, {'path': '/home/jovyan/bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz.sha256', 'bytes': 118, 'sha256': 'd9811fc938a4cbd6fd44c2101ca8dfd5d62f150c888fe76e8346b5dc7b72dc94'}, {'path': '/home/jovyan/bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz.bytes', 'bytes': 7, 'sha256': 'a2c80011fad5c6d004b841cab0f2250364293034d41fade3d2db6a5f564c6ebb'}, {'path': '/home/jovyan/bcsp_spcg_G0_D_training_pending_20261116_v1.tar.gz.contents.sha256', 'bytes': 1260, 'sha256': 'd33abaaf36379f5808040d975545baa28b80ef213984cf57ce0efffd67ec8b3a'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
