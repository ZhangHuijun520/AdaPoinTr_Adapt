import os,socket,json,subprocess,time,hashlib,stat,shutil
from pathlib import Path
t=time.monotonic()
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
assert P.resolve()==P and P.is_dir()
def call(a):return subprocess.check_output(a,cwd=str(P),timeout=8,stderr=subprocess.STDOUT).decode().strip()
p=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1/evidence/server_assets_observation_v1.json');raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='a794ac4ed1e0228bdc65661b19110368967a93f123279989588e5e6ec4d094ad'
expected=json.loads(raw)['assets'];assert len(expected)==30
assets=[];total=0
for r in expected:
 p=Path(r['path']);assert p.is_file() and not p.is_symlink(),str(p)
 for parent in p.parents:assert not parent.is_symlink(),str(parent)
 assert p.stat().st_size==r['bytes'],str(p)
 total+=r['bytes'];assert total<=20*1024**2 and time.monotonic()-t<35
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
 assets.append(r)
print(json.dumps({'status':'SELECTED30_HASH_PASS','assets':assets,'hashed_bytes':total,'server_writes':0,'seconds':time.monotonic()-t}))
