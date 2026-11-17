import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz', 'bytes': 16448, 'sha256': '6179475556febed2323fe99d3269a6c625d49bf54336c1b55542a1cc1d4bf1c2'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz.sha256', 'bytes': 124, 'sha256': '8b0114ab5c3c647899e0e74256ab498225ee33c447a173462f0b4c53c02b1b08'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz.bytes', 'bytes': 7, 'sha256': '3d729279295145e5528fc3a437834a31e12578eaf3db190550e728e64c80358a'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz.contents.sha256', 'bytes': 1125, 'sha256': '2d76c1e24b6e37bff424e2ab90f0a1019b3f446a2edda6d7af0c895a1486311f'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
