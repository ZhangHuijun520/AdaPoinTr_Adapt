import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz', 'bytes': 6744099, 'sha256': 'ac9dbd1007db1ec5d3824684361ce55691bb36aaa41b8f484b5b9b4f37a6a5e4'}, {'path': '/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz.sha256', 'bytes': 109, 'sha256': '8a3e1f8afe1c23f06efbdb0b3dd7f3c4adfe115f90d06c6770214e40cfaa7afe'}, {'path': '/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz.bytes', 'bytes': 9, 'sha256': 'c1f3e02c8afa05ab1f7d76cf2686968a1665904363bc4d3feb7bbf4f19983f42'}, {'path': '/home/jovyan/bcsp_spcg_cuda_pending_20261116_v2.tar.gz.contents.sha256', 'bytes': 1565, 'sha256': 'ba3508efc48ce3aa7bcc4545d3898189d12a4c0b6bf69da4f54a4c8d0b77f0f1'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
