import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz', 'bytes': 18177, 'sha256': '0e7dfa82fc484e7cb355b4513833136483989523974babcaa810099da804d43b'}, {'path': '/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz.sha256', 'bytes': 118, 'sha256': 'c92a790ea8d2a975fd2fd93212d640ce6b4067e363573ef2674d1e0c4b4e0441'}, {'path': '/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz.bytes', 'bytes': 7, 'sha256': 'deddefa395c75147ae9dcefbc521dd3cb16537d3fef4d6b2ff2dce0633f39c78'}, {'path': '/home/jovyan/bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz.contents.sha256', 'bytes': 1038, 'sha256': 'ffdd2d56939664f2635a5914650ac2a5e54bca102d819da5d00308314bcaaa1d'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
