import json,stat,hashlib
from pathlib import Path
p=Path('/home/jovyan/adapointr_work/PoinTr');m=p/'third_party/bcsp_scq_foldC_training_20261113_v1';f=json.loads((m/'fold_binding.json').read_text())['folds'];r={}
for fold in ['C','D']:
 root=p/('data/bcsp_geov1_fold'+fold.lower()+'_8192_seed0_v1/points');assert root.is_dir() and not any(v.is_symlink() for v in (root,*root.parents));rows=[]
 for s in f[fold]['train_sources']:
  for t in ['bilateral','frontoorbital','parietotemporal','random_1','random_2']:
   q=root/('train__'+s.split(':')[1]+'__'+t+'_8192.npz');v=q.lstat();assert stat.S_ISREG(v.st_mode) and v.st_size>0;rows.append([str(q),v.st_size,v.st_mtime_ns])
 assert len(rows)==315;r[fold]=dict(root=str(root),files=len(rows),bytes=sum(x[1] for x in rows),stat_rows_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),rows=rows)
print(json.dumps(r))
