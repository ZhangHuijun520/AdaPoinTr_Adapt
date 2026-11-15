import json,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent
for label in ('metadata_readonly','stat_readiness'):
 cmd=json.loads((S/(label+'_command_v1.json')).read_bytes())['command']
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (S/(label+'_'+k+'_v1.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError('read-only failed stop '+label+' '+repr(r.stdout[-1500:]))
 v=json.loads(r.stdout);print(json.dumps(dict(phase=label,status=v['status'],files=len(v['files']))),flush=True)
