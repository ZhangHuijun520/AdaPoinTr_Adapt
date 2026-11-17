import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz', 'bytes': 18201, 'sha256': '0a6adcb5b8ad0da94b64e6d54fe63d0d1c8609296011cfb7f2a1ee7ffa337154'}, {'path': '/home/jovyan/bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz.sha256', 'bytes': 119, 'sha256': '5f597a42f3fbcba94fc31d57f19d25c735213c74960e333dcd7953ee3ac9015c'}, {'path': '/home/jovyan/bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz.bytes', 'bytes': 7, 'sha256': '06cb7b8c19f9551b6b9fca080e86a25301afc413d2537a56d53131b3e8777530'}, {'path': '/home/jovyan/bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz.contents.sha256', 'bytes': 801, 'sha256': 'c781b998c5555d6fbab9889942a77e31bcb968c153a10860333b5a3eb4909206'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
