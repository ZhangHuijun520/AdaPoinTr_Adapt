"""One read-only identity check, raw byte capture. No secrets or GPU computation."""
import json,subprocess,shlex,sys
from pathlib import Path
A=Path(__file__).resolve().parent
code="import os,socket,json,pathlib,shutil,sys; p=pathlib.Path('/home/jovyan/adapointr_work/PoinTr'); print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),python=str(pathlib.Path(sys.executable).resolve()),version=sys.version.split()[0],project_exists=p.is_dir(),project_link=p.is_symlink(),free_disk_bytes=shutil.disk_usage(p).free)))"
cmd=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',code])
assert len(cmd.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','15','--',cmd],capture_output=True,timeout=30)
for name,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/('identity_readonly_'+name+'_v1.bin')).open('xb') as f:f.write(b)
print(json.dumps(dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8',errors='replace'),stderr=r.stderr.decode('utf-8',errors='replace')),ensure_ascii=True))
if r.returncode:sys.exit(1)
v=json.loads(r.stdout);assert v['hostname']=='shu-common-25721452-notebook-n8xph5-0' and v['uid']==1000 and v['project_exists'] and not v['project_link'] and v['free_disk_bytes']>=4294967296
