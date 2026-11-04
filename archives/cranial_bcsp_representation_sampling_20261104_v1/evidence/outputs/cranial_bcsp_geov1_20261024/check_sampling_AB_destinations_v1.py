"""One bounded non-writing destination check before freezing installation scope."""
from pathlib import Path
import json,subprocess,shlex,hashlib
O=Path(__file__).resolve().parent/'sampling_model_AB_foldC_seed0_20261103_v1'
source="""import os,socket,json
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert p.is_dir();os.chdir(p)
names=['third_party/bcsp_sampling_ab_foldc_seed0_v1','data/bcsp_sampling_ab_foldc_seed0_v1','logs/cranial_bcsp_sampling_ab_v1']
rows=[]
for n in names:
 q=p/n;assert not q.exists() and not q.is_symlink()
 parent=q.parent;assert parent.is_dir() and not any(a.is_symlink() for a in (parent,*parent.parents))
 rows.append(dict(path=str(q),absent=True,parent=str(parent),parent_writable=os.access(parent,os.W_OK)))
assert all(r['parent_writable'] for r in rows)
print(json.dumps(dict(status='ALL_THREE_NEW_ROOTS_ABSENT',targets=rows,server_writes=0)))
"""
cmd='/usr/bin/timeout --signal=TERM --kill-after=2s 20s /opt/conda/bin/python -I -S -B -c '+shlex.quote(source)
assert len(cmd.encode())<=2048
with (O/'destination_readonly_scope_v1.json').open('x') as f:json.dump({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'command_bytes':len(cmd.encode()),'no_retry':True,'server_writes':0},f,indent=2)
p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
with (O/'destination_readonly_result_v1.json').open('x') as f:json.dump({'returncode':p.returncode,'stdout':p.stdout.decode('utf-8',errors='replace'),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest()},f,indent=2)
print('DESTINATION_EXIT',p.returncode)
if p.returncode:raise SystemExit(1)
v=json.loads(p.stdout.decode('utf-8'))
with (O/'destination_readonly_observation_v1.json').open('x') as f:json.dump(v,f,indent=2)
print(json.dumps(v))
