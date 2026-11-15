import json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent
name=sys.argv[1];assert name.isidentifier()
cmd=json.loads((A/'observe_command_v1.json').read_bytes())['command']
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','15','--',cmd],capture_output=True,timeout=25)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/(name+'_'+k+'.bin')).open('xb') as f:f.write(b)
if r.returncode:print(json.dumps(dict(returncode=r.returncode)));sys.exit(1)
x=json.loads(r.stdout);last=None
if x.get('metrics.jsonl'):
 try:last=json.loads(x['metrics.jsonl'].splitlines()[-1])
 except ValueError:pass
print(json.dumps(dict(returncode=0,tmux_present=x['tmux_present'],files=x['files'],exit_code=x.get('exit_code.txt'),failure=x.get('failure.json') or x.get('startup_failure.json'),last_metric=last,log_tail=x.get('launch.log','')[-3500:]),ensure_ascii=True))
