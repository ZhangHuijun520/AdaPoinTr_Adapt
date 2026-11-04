import json,os,socket,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v3')
s='bcsp_geov1_artificial_gpu_zero_update_v3'
out={'tmux_present':subprocess.run(['tmux','has-session','-t',s],capture_output=True).returncode==0,'files':[],'text':{}}
if r.exists():
 assert r.is_dir() and not any(p.is_symlink() for p in (r,*r.parents))
 for name in ('worker.pid','exit_code.txt','summary.json','startup_failure.json','monitor_failure.json','launch.log'):
  p=r/name
  if p.exists():
   assert p.is_file() and not p.is_symlink() and p.stat().st_size<=65536,str(p)
   text=p.read_text(encoding='utf-8');out['files'].append({'name':name,'bytes':p.stat().st_size})
   out['text'][name]=text[-16000:] if name=='launch.log' else text
 p=r/'monitor_events.jsonl'
 if p.exists():
  assert p.is_file() and not p.is_symlink() and p.stat().st_size<=16777216
  lines=p.read_text(encoding='utf-8').splitlines();out['event_count']=len(lines);out['last_event']=json.loads(lines[-1]) if lines else None
 if 'worker.pid' in out['text']:
  pid=int(out['text']['worker.pid']);out['original_pid_present']=Path('/proc/'+str(pid)).exists()
print(json.dumps(out))
