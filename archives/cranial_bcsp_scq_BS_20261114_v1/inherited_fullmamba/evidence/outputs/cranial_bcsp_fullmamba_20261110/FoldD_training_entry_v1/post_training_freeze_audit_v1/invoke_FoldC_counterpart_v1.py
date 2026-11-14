import json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent
cmd=json.loads((D/'counterpart_command_v1.json').read_bytes())['command']
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','95','--',cmd],capture_output=True,timeout=105)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (D/('counterpart_'+k+'_v1.bin')).open('xb') as f:f.write(b)
print(json.dumps(dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8',errors='replace')),ensure_ascii=True));sys.exit(0 if r.returncode==0 else 1)
