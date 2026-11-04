import os,socket,json,stat,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr');c=r/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
ps=[c/'bcsp_training_entry_research_v5.py',c/'bcsp_training_contract_01dt08_v3.py',c/'evidence/research_priority_01dt08_v1',c/'control_train_v3',r/'logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3']
rows=[]
for p in ps:
 for a in p.parents:
  if os.path.lexists(a):assert stat.S_ISDIR(a.lstat().st_mode),'linked parent '+str(a)
 rows.append(dict(path=str(p),exists=os.path.lexists(p),parent_exists=p.parent.is_dir(),parent_writable=os.access(p.parent,os.W_OK|os.X_OK)))
py=subprocess.run(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','--version'],capture_output=True,timeout=5)
tm=subprocess.run(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in8192_seed0_train_v3'],capture_output=True,timeout=5)
print(json.dumps(dict(paths=rows,python=dict(returncode=py.returncode,version=(py.stdout+py.stderr).decode().strip()),tmux_returncode=tm.returncode,server_writes=0,CUDA_calls=0)))
