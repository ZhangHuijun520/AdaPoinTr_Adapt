from pathlib import Path
import os,socket,hashlib,json,time,subprocess,shutil,ast
T=time.monotonic();used=0;seen={};last=None
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
def clean(p):
 p=Path(p);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),str(p);return p
def exact(r):
 global used,last
 p=clean(r['path']);last=str(p)
 if str(p) in seen:
  assert (r['bytes'],r['sha256'])==(seen[str(p)]['bytes'],seen[str(p)]['sha256']);return p
 s=p.stat();assert p.is_file() and s.st_size==r['bytes'],str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):
   used+=len(b);assert used<=805306368 and time.monotonic()-T<55;h.update(b)
 assert h.hexdigest()==r['sha256'],str(p)
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 seen[str(p)]={'path':str(p),'bytes':r['bytes'],'sha256':r['sha256']};assert len(seen)<=96;return p
old=P/'third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
q=json.loads(exact(dict(path=str(old),bytes=18606,sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')).read_bytes())

g=subprocess.run(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
assert g.returncode==0,g.stderr
gpu=[x.strip() for x in g.stdout.strip().split(',')];I=q['identity']
assert gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256
version=subprocess.run([I['python_realpath'],'-I','-S','-B','--version'],capture_output=True,text=True,timeout=5)
assert version.returncode==0 and version.stdout.strip()=='Python '+I['python_version']
assert clean(P).is_dir() and P.resolve()==P and clean(P/'third_party').is_dir()
new=clean(P/'third_party/bcsp_scq_dac_r1_20261115_v1');out=clean(P/'logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')
tm=subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True,timeout=5)
assert tm.returncode in (0,1) and 'bcsp_scq_dac_r1_frozen20_20261115_v1' not in tm.stdout.splitlines()
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k in ('MemTotal','MemAvailable')}
free=shutil.disk_usage(P).free;assert free>=4294967296+982218001
print(json.dumps(dict(status='IDENTITY_RESOURCE_PASS',hostname=socket.gethostname(),uid=os.getuid(),GPU=gpu,python=version.stdout.strip(),free_disk_bytes=free,host_memory=mem,new_root=str(new),seconds=time.monotonic()-T,server_writes=0,CUDA_contexts=0)))
