import hashlib,json,os,socket,sys,time
from pathlib import Path
start=time.monotonic();hostname=socket.gethostname()
assert hostname=='shu-common-25721452-notebook-3x9rq5-0','hostname mismatch: '+hostname
assert os.getuid()==1000,'uid mismatch'
project=Path('/home/jovyan/adapointr_work/PoinTr');os.chdir(project)
assert Path.cwd()==project and not any(p.is_symlink() for p in (project,*project.parents))
assert str(Path(sys.executable).resolve())=='/opt/conda/envs/adapointr-mamba/bin/python3.10' and sys.version.split()[0]=='3.10.20'
B=Path('/home/jovyan');N='bcsp_foldc_8192_train_inputs_v1'
expected=[('.tar.gz',49773476,'fc3c4daa64f7a90ff6396d039c43344ab4d07947d12b675c1ecd4d6c54a08c0d'),('.bytes',9,'30a5e7adafb7d01c0539acac4bb50072a8b36e9a275feb7171d19a67a2c35675'),('.contents.sha256',36108,'1d5f43673c76b93d3195aad25e19de4a229fdc2c23505395d993c548175b823e'),('.contents.sha256.sha256',114,'993be616ec45dd2146441b7c2de31063a6df97e41232def645df3e3d5b4be7ae'),('.tar.gz.sha256',105,'66d75f0c2b1f33966cb71f07a2ef2d942508025b2a5bcfd6c5be0483557f7e71')]
rows=[]
for suffix,size,digest in expected:
 assert time.monotonic()-start<45
 p=B/(N+suffix);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 a=p.stat();assert a.st_size==size,str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 z=p.stat();assert h.hexdigest()==digest and (a.st_size,a.st_mtime_ns,a.st_ino)==(z.st_size,z.st_mtime_ns,z.st_ino),str(p)
 rows.append({'path':str(p),'bytes':size,'sha256':digest})
assert time.monotonic()-start<45
print(json.dumps({'status':'UPLOAD_FIVE_FILES_PASS','hostname':hostname,'uid':os.getuid(),'project':str(project),'files':rows,'seconds':time.monotonic()-start,'server_writes':0}))
