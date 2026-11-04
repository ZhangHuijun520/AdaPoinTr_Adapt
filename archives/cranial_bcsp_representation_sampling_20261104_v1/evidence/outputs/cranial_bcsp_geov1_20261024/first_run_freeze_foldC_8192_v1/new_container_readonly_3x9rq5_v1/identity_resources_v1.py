import datetime,json,os,pwd,shutil,socket,subprocess,sys
from pathlib import Path
host=socket.gethostname();assert host=='shu-common-25721452-notebook-3x9rq5-0',host
assert os.getuid()==1000,'uid mismatch'
p=Path('/home/jovyan/adapointr_work/PoinTr')
assert p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
os.chdir(p);assert Path.cwd()==p
def query(args):
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=10)
 return {'returncode':r.returncode,'stdout':r.stdout[:4096],'stderr':r.stderr[:2048]}
out={'hostname':host,'uid':os.getuid(),'user':pwd.getpwuid(os.getuid()).pw_name,'project':str(Path.cwd()),
 'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bootstrap_python':str(Path(sys.executable).resolve()),
 'bootstrap_python_version':sys.version.split()[0],
 'frozen_python_path':'/opt/conda/envs/adapointr-mamba/bin/python3.10',
 'frozen_python_exists':Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').is_file(),
 'disk':dict(zip(('total','used','free'),shutil.disk_usage(p))),
 'CUDA_VISIBLE_DEVICES_record_only':os.environ.get('CUDA_VISIBLE_DEVICES'),
 'git_metadata_directory_exists':(p/'.git').exists(),'server_writes':0,'model_or_torch_imports':0}
out['GPU']=query(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'])
out['compute_processes']=query(['/usr/bin/nvidia-smi','--query-compute-apps=pid,gpu_uuid','--format=csv,noheader,nounits'])
if out['git_metadata_directory_exists']:
 env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
 r=subprocess.run(['git','-C',str(p),'status','--short','--branch'],env=env,capture_output=True,text=True,timeout=10)
 out['git_status']={'returncode':r.returncode,'stdout':r.stdout[:4096],'stderr':r.stderr[:1024]}
print(json.dumps(out))
