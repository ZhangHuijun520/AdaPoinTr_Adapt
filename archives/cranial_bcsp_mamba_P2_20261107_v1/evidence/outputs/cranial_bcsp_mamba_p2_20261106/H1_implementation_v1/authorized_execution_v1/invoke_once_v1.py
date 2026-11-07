"""Task-local byte-captured WebShell call; no automatic retries."""
import argparse,base64,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('payload');p.add_argument('capture');p.add_argument('--timeout',type=int,default=60);a=p.parse_args()
dst=Path(a.capture)
if dst.exists():raise RuntimeError('capture already exists; no retry')
code=Path(a.payload).read_bytes().decode('utf-8')
if any(len(line.encode())>2048 for line in code.splitlines()):raise ValueError('payload line exceeds 2048 bytes')
command="/opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B <<'P2_H1_PAYLOAD_EOF'\n"+code+"\nP2_H1_PAYLOAD_EOF"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(a.timeout),'--',command]
r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=a.timeout+25)
with dst.open('x',encoding='utf-8') as f:json.dump(dict(returncode=r.returncode,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode()),f,indent=2)
print(r.stdout.decode('utf-8',errors='replace'))
if r.returncode:print(r.stderr.decode('utf-8',errors='replace'),file=sys.stderr)
sys.exit(r.returncode)
