import os,socket,json,stat,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v2')
assert r.is_dir() and not any(x.is_symlink() for x in (r,*r.parents))
rows={}
for name in ['worker.pid','exit_code.txt','failure.json','startup_failure.json','completion.json','metrics.jsonl','resources.jsonl','launch.log']:
 p=r/name
 if not os.path.lexists(p):rows[name]=dict(exists=False);continue
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2147483648
 with p.open('rb') as f:
  f.seek(max(0,s.st_size-8192));raw=f.read(8192)
 rows[name]=dict(exists=True,bytes=s.st_size,tail=raw.decode('utf-8',errors='replace'))
pid=int((r/'worker.pid').read_text().strip())
live=Path('/proc',str(pid)).is_dir()
t=subprocess.run(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in8192_seed0_train_v2'],capture_output=True,timeout=5)
print(json.dumps(dict(worker_pid=pid,worker_live=live,tmux_present=t.returncode==0,artifacts=rows,server_writes=0)))
