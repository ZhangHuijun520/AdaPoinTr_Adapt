import os,socket,json,hashlib,time
from pathlib import Path
s=time.monotonic();h=socket.gethostname();assert h=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents))
n='bcsp_foldc_8192_resource_rebind_supplement_v1';rows=[]
for suffix in ['.tar.gz','.tar.gz.sha256','.bytes','.contents.sha256','.contents.sha256.sha256','.installation_map.json','.installation_map.json.sha256']:
 p=Path('/home/jovyan')/(n+suffix);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size<=65536
 raw=p.read_bytes();rows.append(dict(filename=p.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
assert time.monotonic()-s<25
print(json.dumps(dict(status='UPLOAD_SEVEN_FILES_OBSERVED',hostname=h,uid=os.getuid(),files=rows,server_writes=0,seconds=time.monotonic()-s)))
