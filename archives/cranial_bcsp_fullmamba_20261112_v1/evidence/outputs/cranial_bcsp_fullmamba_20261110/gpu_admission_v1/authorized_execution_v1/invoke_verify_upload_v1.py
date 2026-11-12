import subprocess,json,sys,hashlib
from pathlib import Path
A=Path(__file__).resolve().parent
cmd=json.loads((A/'verify_upload_command_v1.json').read_bytes())['command']
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--',cmd],capture_output=True,timeout=40)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (A/('verify_upload_'+k+'_v1.bin')).open('xb') as f:f.write(b)
with (A/'verify_upload_call_v1.json').open('x') as f:json.dump(dict(returncode=r.returncode,read_only=True),f)
print(json.dumps(dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8',errors='replace')),ensure_ascii=True))
sys.exit(0 if r.returncode==0 else 1)
