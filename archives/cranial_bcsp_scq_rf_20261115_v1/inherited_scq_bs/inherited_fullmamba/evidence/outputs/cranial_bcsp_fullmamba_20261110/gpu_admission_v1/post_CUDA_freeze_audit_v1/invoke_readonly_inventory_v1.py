import subprocess,json,sys
from pathlib import Path
D=Path(__file__).resolve().parent
cmd=json.loads((D/'inventory_command_v1.json').read_bytes())['command']
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--',cmd],capture_output=True,timeout=40)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (D/('inventory_'+sys.argv[1]+'_'+k+'.bin')).open('xb') as f:f.write(b)
if r.returncode:print(json.dumps(dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8',errors='replace'))));sys.exit(1)
x=json.loads(r.stdout);print(json.dumps(dict(returncode=0,files=len(x['rows']),bytes=x['bytes'],dirs=x['dirs'],tmux_present=x['tmux_present'],worker_PID_exists=x['worker_PID_exists'])))
