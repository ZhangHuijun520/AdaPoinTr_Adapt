import os,socket,json,subprocess,datetime,time
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
def cmd(args):
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 return dict(returncode=r.returncode,stdout=r.stdout.decode(),stderr=r.stderr.decode())
g=cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
p=cmd(['/usr/bin/nvidia-smi','--query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory','--format=csv,noheader,nounits'])
t=cmd(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in8192_seed0_train_v1'])
pid=Path('/proc/922');state=None
if pid.exists():
 fields={}
 for line in (pid/'status').read_text().splitlines():
  k,v=line.split(':',1)
  if k in ['Name','State','PPid','Uid']:fields[k]=v.strip()
 state=fields
print(json.dumps(dict(hostname=socket.gethostname(),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),gpu=g,compute_processes=p,tmux=t,PID922_present=pid.exists(),PID922_status=state,meaning='Current snapshot only; not historical peak or process attribution at failure',server_writes=0)))
