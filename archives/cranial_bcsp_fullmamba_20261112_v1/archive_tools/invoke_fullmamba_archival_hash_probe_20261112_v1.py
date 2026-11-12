"""One bounded read-only hash probe through the existing WebShell client."""
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent.parent;O=R/'outputs/cranial_bcsp_fullmamba_20261110/final_archival_20261112_v1'
cmd=json.loads((O/'remote_hash_command_v1.json').read_bytes())['command']
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','180','--',cmd],capture_output=True,timeout=195)
for name,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (O/('remote_hash_'+name+'_v1.bin')).open('xb') as f:f.write(b)
assert r.returncode==0,('READONLY_PROBE_FAILED_NO_AUTOMATIC_RETRY',r.returncode,r.stdout.decode('utf-8',errors='replace')[:2000])
j=json.loads(r.stdout);assert j['status']=='FROZEN_ARCHIVAL_ASSETS_READONLY_REHASH_PASS'
with (O/'remote_hash_verification_v1.json').open('x',encoding='utf-8') as f:json.dump(j,f,ensure_ascii=False,indent=2)
print(json.dumps(j))
