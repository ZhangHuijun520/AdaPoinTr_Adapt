"""Bounded status observation only; no formal freeze audit, GPU query, imports or forward."""
from pathlib import Path
import ast,base64,json,shlex,subprocess,sys,zlib
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_dac_r01_preparation_20261115_v1/authorized_execution_v1'
label=sys.argv[1];assert label.isdigit()
source='''from pathlib import Path
import os,socket,json,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0'
p=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')
assert not any(x.is_symlink() for x in (p,*p.parents))
def tail(path,n=12000):
 if not path.exists():return None
 with path.open('rb') as f:f.seek(max(0,path.stat().st_size-n));return f.read(n).decode(errors='replace')
x=subprocess.run(['tmux','has-session','-t','bcsp_scq_dac_r1_frozen20_20261115_v1'],capture_output=True,timeout=5)
v=dict(hostname=socket.gethostname(),tmux_exists=x.returncode==0,output_exists=p.exists(),server_writes=0,new_forward=0,formal_audit=False)
if p.exists():
 v['files']=[f.name for f in p.iterdir()];v['launch_log_tail']=tail(p/'launch.log')
 for name in ('failure.json','completion.json','diagnostic_complete.json'):
  f=p/name
  if f.exists():v[name]=json.loads(f.read_bytes())
 if (p/'exit_code.txt').exists():v['exit_code']=(p/'exit_code.txt').read_text().strip()
 if (p/'worker.pid').exists():
  pid=int((p/'worker.pid').read_text());proc=Path('/proc')/str(pid)
  try:v['worker_live']=b'bcsp_scq_dac_r1_entry_v1.py' in (proc/'cmdline').read_bytes()
  except FileNotFoundError:v['worker_live']=False
 lines=(tail(p/'calls.jsonl') or '').splitlines()
 v['last_call_claim']=None
 for line in reversed(lines):
  try:v['last_call_claim']=json.loads(line);break
  except ValueError:pass
 v['case_files']=len(list((p/'cases').glob('*.npz'))) if (p/'cases').exists() else 0
 v['resource_tail']=tail(p/'resources.jsonl',5000)
print(json.dumps(v))
'''
ast.parse(source,feature_version=(3,8));blob=base64.b85encode(zlib.compress(source.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048
x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=45)
for k,b in [('stdout',x.stdout),('stderr',x.stderr)]:
 with (O/('observation_'+label+'_'+k+'.bin')).open('xb') as f:f.write(b)
assert x.returncode==0,(x.returncode,x.stdout.decode(errors='replace')[-1500:])
v=json.loads(x.stdout)
with (O/('observation_'+label+'.json')).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
print(json.dumps(v,ensure_ascii=True))
