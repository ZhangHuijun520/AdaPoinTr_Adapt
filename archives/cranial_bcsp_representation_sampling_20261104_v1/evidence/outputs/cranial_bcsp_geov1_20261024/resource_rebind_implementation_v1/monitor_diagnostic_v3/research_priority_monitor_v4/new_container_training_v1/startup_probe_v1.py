import os,socket,json,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3')
def tail(name,n=4096):
 f=p/name
 if not f.is_file():return None
 assert not f.is_symlink()
 with f.open('rb') as s:s.seek(max(0,f.stat().st_size-n));return s.read(n).decode(errors='replace')
def last(name):
 text=tail(name)
 if not text:return None
 for line in reversed(text.splitlines()):
  try:return json.loads(line)
  except ValueError:pass
 return None
pid=tail('worker.pid',64);pid=int(pid.strip()) if pid else None
tm=subprocess.run(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in8192_seed0_train_v3'],capture_output=True,timeout=5)
gpu=subprocess.run(['/usr/bin/nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,timeout=10)
failure={k:tail(k) for k in ['failure.json','startup_failure.json']}
print(json.dumps(dict(tmux_present=tm.returncode==0,worker_pid=pid,worker_live=bool(pid and Path('/proc/'+str(pid)).is_dir()),exit_code=tail('exit_code.txt',64),last_metric=last('metrics.jsonl'),last_resource=last('resources.jsonl'),failure=failure,completion_present=(p/'completion.json').is_file(),GPU=gpu.stdout.decode().strip(),log_tail=tail('launch.log',2000) if any(failure.values()) else None,server_writes=0,extra_forward_calls=0)))
