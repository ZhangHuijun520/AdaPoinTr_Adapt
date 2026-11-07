import hashlib,json,os,pathlib,shutil,socket,subprocess
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldD_20261106_v1')
Q='305ce3380ae7b951c7180907f63842abc51eae5d9dec817e2a5ad89718fdd390'
p=R/'M_H1_foldD_seed0_training_execution_request_v1.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==Q
q=json.loads(p.read_bytes());c=q['launch_contract'];I=q['identity']
assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']
out=pathlib.Path(q['output']);claim=pathlib.Path(q['launch_attempt'])
for p in (out,claim,*out.parents,*claim.parents):assert not p.is_symlink(),str(p)
assert not out.exists() and not claim.exists() and shutil.disk_usage(R).free>=4294967296
for key,h in [('authorization','b16e457cb2d73f8b68f57e3656034f24a062a5169d1df576a86f95ed7d9af838'),('runtime','ab87bdb3713c812526d44e2e9e085bf8c36f0b28e00580b688d635e2b4d86a4c'),('launcher','6bc53101310b423ab5c050b7530a344c16a115755f0531d887540a7152662aff')]:
 p=pathlib.Path(c[key]);assert not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==h
check=subprocess.run(['tmux','has-session','-t',c['tmux_session']],capture_output=True,timeout=10);assert check.returncode==1
gpu=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
v=[s.strip() for s in gpu.stdout.strip().split(',')]
assert gpu.returncode==0 and v[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256
pids=subprocess.run(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10);assert pids.returncode==0 and not pids.stdout.strip()
subprocess.run(['/bin/bash','-n',c['launcher']],check=True,capture_output=True,timeout=10)
with claim.open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=Q),f);f.flush();os.fsync(f.fileno())
r=subprocess.run(['tmux','new-session','-d','-s',c['tmux_session'],'/bin/bash '+c['launcher']],capture_output=True,text=True,timeout=15)
print(json.dumps(dict(status='UNIQUE_TMUX_SUBMITTED' if r.returncode==0 else 'LAUNCH_FAILED_STOP',returncode=r.returncode,session=c['tmux_session'],claim_consumed=True,stderr=r.stderr)),flush=True)
assert r.returncode==0
