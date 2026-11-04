import hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert socket.gethostname()=="shu-common-25721452-notebook-o9mz8z-0" and os.getuid()==1000
root=Path("/home/jovyan/adapointr_work/PoinTr")
assert root.is_dir() and root.resolve()==root
assert str(Path(sys.executable).resolve())=="/opt/conda/envs/adapointr-mamba/bin/python3.10"
assert sys.version.split()[0]=="3.10.20"
rows=[{"path":"/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch/version.py","bytes":248,"sha256":"b10649fd636e7404398d608b84a2cacc6645e3952f043b439d4c50c95a26a1b5"},{"path":"/opt/conda/envs/adapointr-mamba/bin/python3.10","bytes":17331920,"sha256":"01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d"},{"path":"/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch-2.4.1+cu118.dist-info/METADATA","bytes":26707,"sha256":"11606497a9792f0d040ad062064ee1c024dde8b10fc38bed361134d0b7ec429a"},{"path":"/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA","bytes":40196,"sha256":"b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4"},{"path":"/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA","bytes":62026,"sha256":"22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a"}]
for r in rows:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'],str(p)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
print(json.dumps({'status':'PASS','hashes':rows}))
