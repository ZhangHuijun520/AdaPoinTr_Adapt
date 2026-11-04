import os,socket,json,hashlib,time,stat
from pathlib import Path
s=time.monotonic();h=socket.gethostname();assert h=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr');assert all(stat.S_ISDIR(x.lstat().st_mode) for x in (r,*r.parents))
n='bcsp_foldc_8192_monitor_diagnostic_v3_supplement_v1';rows=[]
for suffix in ['.bytes','.contents.sha256','.contents.sha256.sha256','.installation_map.json','.installation_map.json.sha256','.tar.gz','.tar.gz.sha256']:
 p=Path('/home/jovyan')/(n+suffix);assert all(stat.S_ISDIR(x.lstat().st_mode) for x in p.parents)
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_size<=65536
 raw=p.read_bytes();end=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(end.st_size,end.st_mtime_ns,end.st_ino)
 rows.append(dict(filename=p.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
 assert time.monotonic()-s<20
print(json.dumps(dict(status='UPLOAD_SEVEN_FILES_OBSERVED',hostname=h,uid=1000,files=rows,server_writes=0,seconds=time.monotonic()-s)))
