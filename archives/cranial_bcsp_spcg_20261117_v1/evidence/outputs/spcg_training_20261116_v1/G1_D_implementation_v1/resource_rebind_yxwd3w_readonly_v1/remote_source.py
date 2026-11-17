from pathlib import Path
import os,json,socket,hashlib,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');assert not any(x.is_symlink() for x in (p,*p.parents));s=os.statvfs(p)
r=dict(hostname=socket.gethostname(),uid=os.getuid(),available_bytes=s.f_bavail*s.f_frsize,required_bytes=int(8.5*1024**3),uploads=[],targets=[])
for x in [{'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz', 'bytes': 19608, 'sha256': '9001fdb12f38fff185f86affbef8c9a7c5cbb136c7c1b70992c1756d4645a235'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz.sha256', 'bytes': 118, 'sha256': '2e56605844a1cb400c57bc337251f0c0228891790ade9ccee994ed5ad16d4b41'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz.bytes', 'bytes': 7, 'sha256': '458dbd705225e4e576dafe30ec7a146117f949f3f76592240f4c3f7018df253d'}, {'path': '/home/jovyan/bcsp_spcg_G1_D_training_pending_20261117_v1.tar.gz.contents.sha256', 'bytes': 1038, 'sha256': 'de8c572169fbf7c16df9649d627b206fd2fc89e4374f4d20d97860603996a3fc'}]:
 f=Path(x['path']);v=dict(path=str(f),exists=f.exists(),linked=any(y.is_symlink() for y in (f,*f.parents)))
 if v['exists'] and not v['linked']:v.update(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest());v['matches']=v['bytes']==x['bytes'] and v['sha256']==x['sha256']
 r['uploads'].append(v)
for name in ['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1D_training_20261117_v1', '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldD_seed0_train_20261117_v1']:
 f=Path(name);r['targets'].append(dict(path=name,exists=f.exists(),linked=any(x.is_symlink() for x in (f,*f.parents))))
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10);r['GPU']=dict(returncode=g.returncode,stdout=g.stdout.decode(errors='replace'),stderr=g.stderr.decode(errors='replace'))
print(json.dumps(r))
