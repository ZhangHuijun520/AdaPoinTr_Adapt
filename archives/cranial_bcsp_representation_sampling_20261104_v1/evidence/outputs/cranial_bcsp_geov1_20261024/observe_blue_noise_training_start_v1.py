"""Read-only startup confirmation; does not restart or modify the training."""
import base64,hashlib,json,shlex,subprocess,zlib
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';A=O/'authorized_execution_v1'
scope=json.loads((O/'Euclidean_training_execution_request_v1.json').read_bytes())
raw=("""import os,json,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
P=Path(OUTPUT)
def tail(p,n):
 if not p.is_file():return None
 assert not p.is_symlink()
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-n));return f.read(n).decode('utf-8',errors='replace')
v={'hostname':socket.gethostname(),'output':str(P),'files':sorted(p.name for p in P.iterdir()) if P.exists() else [],'exit_code':tail(P/'exit_code.txt',64),'worker_pid':tail(P/'worker.pid',32),'metrics_tail':tail(P/'metrics.jsonl',2500),'resource_tail':tail(P/'resources.jsonl',1800),'log_tail':tail(P/'launch.log',4000),'failure':tail(P/'failure.json',4000),'startup_failure':tail(P/'startup_failure.json',4000),'completion':tail(P/'completion.json',5000),'tmux_present':subprocess.run(['tmux','has-session','-t',SESSION],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5).returncode==0,'server_writes':0}
if v['worker_pid']:
 pid=v['worker_pid'].strip();v['worker_live']=pid.isdigit() and Path('/proc/'+pid).is_dir()
print(json.dumps(v))
""").replace('OUTPUT',repr(scope['future_paths']['output'])).replace('SESSION',repr(scope['future_paths']['tmux'])).encode()
encoded=base64.b64encode(zlib.compress(raw,9)).decode()
code="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+encoded+"')))"
command='/usr/bin/timeout 20s /opt/conda/bin/python -I -S -B -c '+shlex.quote(code)
assert len(command.encode())<=2048
with (A/'startup_observation_scope_v1.json').open('x') as f:json.dump({'source_sha256':hashlib.sha256(raw).hexdigest(),'max_command_bytes':2048,'readonly':True},f,indent=2)
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',command],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
with (A/'startup_observation_capture_v1.json').open('x') as f:json.dump({'returncode':r.returncode,'stdout_base64':base64.b64encode(r.stdout).decode(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()},f,indent=2)
assert r.returncode==0
v=json.loads(r.stdout.decode('utf-8'))
with (A/'startup_observation_v1.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v))
