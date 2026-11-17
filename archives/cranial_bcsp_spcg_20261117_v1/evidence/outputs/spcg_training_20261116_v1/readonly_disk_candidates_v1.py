"""Bounded metadata-only disk inventory; no deletion, CUDA, model or payload reads."""
from pathlib import Path
import json,subprocess,base64,zlib
S=Path(__file__).resolve().parent;O=S/'disk_readonly_review_v1';O.mkdir()
code="""from pathlib import Path
import json,os,socket,subprocess,stat,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');h=Path('/home/jovyan');s=os.statvfs(p)
r=dict(hostname=socket.gethostname(),available_bytes=s.f_bavail*s.f_frsize,total_bytes=s.f_blocks*s.f_frsize,required_bytes=int(8.5*1024**3),home_files=[],home_dirs=[])
for x in h.iterdir():
 if x.name.startswith('.'):continue
 t=x.lstat()
 if stat.S_ISREG(t.st_mode):r['home_files'].append(dict(path=str(x),bytes=t.st_size,mtime_ns=t.st_mtime_ns))
 elif stat.S_ISDIR(t.st_mode):r['home_dirs'].append(x.name)
def run(args,seconds):
 try:
  c=subprocess.run(args,capture_output=True,timeout=seconds);return dict(returncode=c.returncode,stdout=c.stdout.decode(errors='replace'),stderr=c.stderr.decode(errors='replace'))
 except subprocess.TimeoutExpired:return dict(timeout=True)
r['project_du']=run(['du','-x','-B1','--max-depth=2',str(p)],30)
r['tmux']=run(['tmux','list-sessions','-F','#{session_name}'],5)
print(json.dumps(r))
"""
compile(code,'disk_inventory','exec');(O/'remote_source.py').write_text(code,encoding='utf-8')
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))"
a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(a).encode())<=2048
v=subprocess.run(a,capture_output=True,timeout=50);(O/'stdout.bin').write_bytes(v.stdout);(O/'stderr.bin').write_bytes(v.stderr);assert v.returncode==0,v.returncode
d=json.loads(v.stdout);(O/'inventory_v1.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
rows=[]
for line in d['project_du'].get('stdout','').splitlines():
 size,path=line.split('\t',1);rows.append((int(size),path))
print(json.dumps(dict(available_GiB=d['available_bytes']/1024**3,shortfall_GiB=max(0,d['required_bytes']-d['available_bytes'])/1024**3,largest=sorted(rows,reverse=True)[:30],home_files=d['home_files'],tmux=d['tmux']),ensure_ascii=False))
