import os,socket,json,subprocess
from pathlib import Path
p=Path('/home/jovyan/adapointr_work/PoinTr');assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
assert p.resolve()==p and p.is_dir();os.chdir(p)
s=os.statvfs(p)
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader'],capture_output=True,timeout=5)
t=subprocess.run(['git','status','--short','--untracked-files=no'],capture_output=True,timeout=5)
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),cwd=os.getcwd(),available_bytes=s.f_bavail*s.f_frsize,gpu_returncode=g.returncode,gpu_stdout=g.stdout.decode(errors='replace'),gpu_stderr=g.stderr.decode(errors='replace'),git_returncode=t.returncode,git_stdout=t.stdout.decode(errors='replace')[:8000],git_stderr=t.stderr.decode(errors='replace')[:1000])))
