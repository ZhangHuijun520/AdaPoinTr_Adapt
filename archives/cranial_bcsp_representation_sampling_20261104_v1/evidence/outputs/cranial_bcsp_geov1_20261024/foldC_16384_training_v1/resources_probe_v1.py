import os,socket,json,shutil,subprocess,time,datetime,stat
from pathlib import Path
s=time.monotonic();h=socket.gethostname();assert h=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert all(stat.S_ISDIR(x.lstat().st_mode) for x in (p,*p.parents))
def query(args):
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 return dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8'),stderr=r.stderr.decode('utf-8'))
gpu=query(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'])
procs=query(['/usr/bin/nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_gpu_memory','--format=csv,noheader,nounits'])
mem={}
for line in Path('/proc/meminfo').read_text().splitlines():
 k,v=line.split(':',1)
 if k in ('MemTotal','MemAvailable'):mem[k+'_bytes']=int(v.split()[0])*1024
disk=shutil.disk_usage(p)
print(json.dumps(dict(hostname=h,uid=os.getuid(),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),disk=dict(total=disk.total,used=disk.used,free=disk.free),memory=mem,cpu_count=os.cpu_count(),gpu=gpu,compute_processes=procs,CUDA_VISIBLE_DEVICES_record_only=os.environ.get('CUDA_VISIBLE_DEVICES'),server_writes=0,seconds=time.monotonic()-s)))
