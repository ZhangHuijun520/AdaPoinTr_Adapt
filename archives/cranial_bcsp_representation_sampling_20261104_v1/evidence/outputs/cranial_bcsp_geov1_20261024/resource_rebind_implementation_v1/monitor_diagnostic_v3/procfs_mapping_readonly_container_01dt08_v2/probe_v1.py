import os,json,socket,time
from pathlib import Path
s=time.monotonic()
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
def read(p,n):
 with open(p,'rb') as f:b=f.read(n+1)
 assert len(b)<=n
 return b.decode('ascii')
rows=[]
for line in read('/proc/self/mountinfo',262144).splitlines():
 a=line.split();i=a.index('-')
 if a[i+1]=='proc':
  rows.append(dict(id=a[0],parent=a[1],device=a[2],root=a[3],mountpoint=a[4],options=a[5],filesystem=a[i+1],source=a[i+2],super_options=a[i+3]))
assert len(rows)<=32
keys={'Pid','Tgid','PPid','Uid','NSpid','NStgid'}
status={}
for line in read('/proc/self/status',16384).splitlines():
 k,v=line.split(':',1)
 if k in keys:status[k]=v.strip()
ns={k:os.readlink('/proc/self/ns/'+k) for k in ['pid','pid_for_children','mnt','user']}
assert int(status['Tgid'])==os.getpid()
elapsed=time.monotonic()-s
assert elapsed<10
r=dict(hostname=socket.gethostname(),uid=os.getuid(),self_pid=os.getpid(),status=status,namespaces=ns,procfs_mounts=rows,elapsed_seconds=elapsed,server_writes=0,CUDA_contexts_created=0,candidate_paths_opened=0)
out=json.dumps(r);assert len(out.encode())<=65536
print(out)
