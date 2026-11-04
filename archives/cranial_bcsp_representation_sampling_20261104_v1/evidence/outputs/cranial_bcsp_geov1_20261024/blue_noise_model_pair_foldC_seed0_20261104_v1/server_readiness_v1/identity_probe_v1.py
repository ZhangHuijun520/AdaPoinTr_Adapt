import os,socket,json,subprocess,time,hashlib,stat,shutil
from pathlib import Path
t=time.monotonic()
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
assert P.resolve()==P and P.is_dir()
def call(a):return subprocess.check_output(a,cwd=str(P),timeout=8,stderr=subprocess.STDOUT).decode().strip()
roots=[P/'third_party/bcsp_blue_noise_ab_foldc_seed0_v1',P/'data/bcsp_blue_noise_ab_foldc_seed0_v1',P/'logs/cranial_bcsp_blue_noise_ab_v1']
parents={}
for x in roots:
 assert not x.exists() and not x.is_symlink(),str(x)
 for y in x.parents:
  assert not y.is_symlink(),str(y)
 parents[str(x.parent)]={'is_directory':x.parent.is_dir(),'writable':os.access(x.parent,os.W_OK)}
v={'hostname':socket.gethostname(),'uid':os.getuid(),'project':str(P),'disk_free':shutil.disk_usage(P).free,'gpu':call(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader']),'compute':call(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader']),'python_exists':Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').is_file(),'python_realpath':str(Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').resolve()),'python_version':call(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','--version']),'new_roots_absent':[str(x) for x in roots],'parents':parents,'git_head':call(['git','rev-parse','HEAD']),'git_status':call(['git','status','--short']),'memory':Path('/proc/meminfo').read_text().splitlines()[:3],'tmux_sessions':subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True,timeout=5).stdout.strip(),'server_writes':0}
assert v['disk_free']>4*1024**3 and not v['compute']
print(json.dumps(v))
