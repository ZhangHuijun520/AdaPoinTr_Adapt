import json,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0'
out=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/M0_foldD_seed0_train_20261106_v1')
def text(name,cap=10000):
 p=out/name
 return p.read_text(errors='replace')[-cap:] if p.is_file() else None
count=0;last=None
p=out/'metrics.jsonl'
if p.is_file():
 with p.open() as f:
  for line in f:
   if line.strip():count+=1;last=json.loads(line)
resource=None;p=out/'resources.jsonl'
if p.is_file():
 with p.open() as f:
  for line in f:
   if line.strip():resource=json.loads(line)
pid=text('worker.pid',64);live=False
if pid:
 p=Path('/proc')/pid.strip()/'cmdline';live=p.is_file() and b'bcsp_p1_foldD_training_entry_v1.py' in p.read_bytes()
print(json.dumps(dict(session_present=subprocess.run(['tmux','has-session','-t','bcsp_p1_M0_D_seed0_20261106_v1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0,worker_pid=pid,worker_live=live,exit_code=text('exit_code.txt',64),committed_metric_records=count,last_metric=last,last_resource=resource,run_identity=text('run_identity.json',5000),completion=text('completion.json',5000),failure=text('failure.json',5000),startup_failure=text('startup_failure.json',5000),log_tail=text('launch.log',3500))),flush=True)
