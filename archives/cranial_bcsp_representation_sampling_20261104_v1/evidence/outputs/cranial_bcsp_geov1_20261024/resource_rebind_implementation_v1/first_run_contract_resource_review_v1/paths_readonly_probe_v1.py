import os,socket,json,hashlib,stat,subprocess,time
from pathlib import Path
s=time.monotonic();assert socket.gethostname()=='shu-common-25721452-notebook-3x9rq5-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr');c=r/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1';out=r/'logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v1';rows=[]
for p in [out,c/'control']:
 for x in p.parents:
  if os.path.lexists(x):assert stat.S_ISDIR(x.lstat().st_mode),'linked/invalid parent: '+str(x)
 a=p.parent
 while not os.path.lexists(a):a=a.parent
 rows.append(dict(path=str(p),exists=os.path.lexists(p),nearest_existing_parent=str(a),parent_writable=os.access(a,os.W_OK|os.X_OK)))
p=Path('/opt/conda/envs/adapointr-mamba/bin/python3.10')
assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
raw=p.read_bytes();assert len(raw)==17331920 and hashlib.sha256(raw).hexdigest()=='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'
v=subprocess.run([str(p),'-I','-S','-B','--version'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
t=subprocess.run(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in8192_seed0_train_v1'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5)
print(json.dumps(dict(paths=rows,python=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),executable=os.access(p,os.X_OK),returncode=v.returncode,version=(v.stdout+v.stderr).decode()),tmux=dict(returncode=t.returncode,stdout=t.stdout.decode(),stderr=t.stderr.decode()),server_writes=0,seconds=time.monotonic()-s)))
