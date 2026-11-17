from pathlib import Path
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
