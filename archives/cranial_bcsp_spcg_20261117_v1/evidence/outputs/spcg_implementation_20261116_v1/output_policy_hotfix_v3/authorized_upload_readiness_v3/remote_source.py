import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_output_policy_pending_20261116_v3.tar.gz', 'bytes': 20806, 'sha256': '7b394f97af4edbb68aefd202e90e4ac497d10d56efef4565d9fff2696228e400'}, {'path': '/home/jovyan/bcsp_spcg_output_policy_pending_20261116_v3.tar.gz.sha256', 'bytes': 118, 'sha256': 'd74dfcdbf9c2c6ac4ab2eb35d1098ce978af9a3b2024c36e55b6443e1c0fd797'}, {'path': '/home/jovyan/bcsp_spcg_output_policy_pending_20261116_v3.tar.gz.bytes', 'bytes': 7, 'sha256': '86b123c4f0a7e096917d79bd3aba3c974362cba238d6c1d1556c92c6602400f3'}, {'path': '/home/jovyan/bcsp_spcg_output_policy_pending_20261116_v3.tar.gz.contents.sha256', 'bytes': 1116, 'sha256': 'fb0e115dbfc353fd093cacd8d28e80dd1507d251854067b59ef7a50ceab54869'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
