from pathlib import Path
import subprocess,json,base64,zlib
V=Path(__file__).resolve().parent;O=V/'authorized_disk_gate_v1';O.mkdir()
code="""import os,socket,json
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert not any(x.is_symlink() for x in (p,*p.parents))
s=os.statvfs(p);free=s.f_bavail*s.f_frsize;required=int(8.5*1024**3)
print(json.dumps(dict(hostname=socket.gethostname(),available_bytes=free,required_bytes=required,pass_disk_gate=free>=required,shortfall_bytes=max(0,required-free),server_writes=0)))
"""
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))"
a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--','/usr/bin/python3','-I','-S','-B','-c',c]
r=subprocess.run(a,capture_output=True,timeout=25);(O/'stdout.bin').write_bytes(r.stdout);(O/'stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/'result.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps(d))
