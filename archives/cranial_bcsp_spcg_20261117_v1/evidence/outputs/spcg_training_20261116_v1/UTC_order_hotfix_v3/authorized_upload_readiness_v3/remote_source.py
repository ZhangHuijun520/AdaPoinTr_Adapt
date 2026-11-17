import socket,os,json,hashlib
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
rows=[{'path': '/home/jovyan/bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz', 'bytes': 13933, 'sha256': '0c1891dd121c5763411e9d3278e3e6b92f44409e4ce43bd3f36ad272493099bb'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz.sha256', 'bytes': 119, 'sha256': 'a991f71fb976d1a93c824bf4963d900aa4c86eb9a1cc137865e9e2f3366006fe'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz.bytes', 'bytes': 7, 'sha256': 'c324d03cb7cb382ab7737b843168ff995c5dd3f23eb442baba653afe4ae7afab'}, {'path': '/home/jovyan/bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz.contents.sha256', 'bytes': 914, 'sha256': '6300d7d9b3b6661d342319288521f8cee62bfd7536d8748141b793dacc693f27'}]
result=[]
for r in rows:
 p=Path(r['path']);v=dict(path=str(p),exists=p.exists(),linked=any(x.is_symlink() for x in (p,*p.parents)))
 if v['exists'] and not v['linked']:
  v.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest());v['matches']=v['bytes']==r['bytes'] and v['sha256']==r['sha256']
 result.append(v)
print(json.dumps(dict(hostname=socket.gethostname(),uploads=result)))
