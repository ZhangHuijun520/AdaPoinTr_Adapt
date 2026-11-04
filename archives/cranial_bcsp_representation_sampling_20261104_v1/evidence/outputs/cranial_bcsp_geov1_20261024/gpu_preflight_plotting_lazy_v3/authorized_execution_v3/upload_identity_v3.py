import os,socket,sys,json,subprocess,shutil
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0','hostname mismatch'
assert os.getuid()==1000,'uid mismatch'
p=Path('/home/jovyan/adapointr_work/PoinTr');os.chdir(p);assert Path.cwd()==p
assert str(Path(sys.executable).resolve())=='/opt/conda/envs/adapointr-mamba/bin/python3.10' and sys.version.split()[0]=='3.10.20','Python identity'
u='GPU-2f32f6fb-ea5d-730a-4ea2-2f6063e31065'
def smi(q):return subprocess.check_output(['/usr/bin/nvidia-smi','--id='+u,q,'--format=csv,noheader,nounits'],text=True,timeout=10).strip()
g=smi('--query-gpu=uuid,name,driver_version,memory.total,memory.used');a=[x.strip() for x in g.split(',')]
assert a[:4]==[u,'NVIDIA GeForce RTX 4090 D','575.51.03','24564'] and int(a[4])<=256,'GPU identity/idle'
assert not smi('--query-compute-apps=pid'),'GPU occupied'
assert shutil.disk_usage(p).free>=2147483648,'disk budget'
print(json.dumps({'status':'IDENTITY_RESOURCE_PASS','hostname':socket.gethostname(),'uid':os.getuid(),'cwd':str(p),'GPU':g,'free_bytes':shutil.disk_usage(p).free,'server_writes':0}))
