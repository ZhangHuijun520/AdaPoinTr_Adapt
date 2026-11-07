"""Fixed-task raw-byte Base64 WebShell transport; one invocation, no retry."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('payload');p.add_argument('capture');p.add_argument('--timeout',type=int,default=55);a=p.parse_args()
dst=Path(a.capture)
if dst.exists():raise RuntimeError('capture already exists')
raw=Path(a.payload).read_bytes();encoded=base64.b64encode(raw).decode('ascii')
assert base64.b64decode(encoded)==raw
command='/opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B -c "import base64;exec(base64.b64decode(\''+encoded+'\'))"'
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(a.timeout),'--',command]
try:
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=a.timeout+20)
 code,out,err=r.returncode,r.stdout,r.stderr
except subprocess.TimeoutExpired as e:
 code,out,err=124,e.stdout or b'',e.stderr or b''
record=dict(returncode=code,payload_sha256=hashlib.sha256(raw).hexdigest(),command_bytes=len(command.encode()),stdout_base64=base64.b64encode(out).decode(),stderr_base64=base64.b64encode(err).decode())
with dst.open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
print(out.decode('utf-8',errors='replace'))
if code:print('TRANSPORT_FAILED_STOP returncode='+str(code),file=sys.stderr)
sys.exit(code)
