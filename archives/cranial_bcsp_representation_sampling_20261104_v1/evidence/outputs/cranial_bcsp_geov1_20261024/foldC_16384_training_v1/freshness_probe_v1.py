import os,socket,json,stat,subprocess
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-01dt08-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr');c=r/'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
ps=[r/'data/bcsp_geov1_foldc_16384_seed0_v1',c/'evidence/qualified_data_qc_foldC_16384_v1.json',c/'control_train_foldC_16384_v1',r/'logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1']
rows=[]
for p in ps:
 for a in p.parents:
  if os.path.lexists(a):assert stat.S_ISDIR(a.lstat().st_mode),'parent '+str(a)
 rows.append(dict(path=str(p),exists=os.path.lexists(p),parent_writable=os.access(p.parent,os.W_OK|os.X_OK)))
tm=subprocess.run(['/usr/bin/tmux','has-session','-t','bcsp_geov1_b0_foldc_in16384_seed0_train_v1'],capture_output=True,timeout=5)
print(json.dumps(dict(paths=rows,tmux_returncode=tm.returncode,server_writes=0,CUDA_calls=0)))
