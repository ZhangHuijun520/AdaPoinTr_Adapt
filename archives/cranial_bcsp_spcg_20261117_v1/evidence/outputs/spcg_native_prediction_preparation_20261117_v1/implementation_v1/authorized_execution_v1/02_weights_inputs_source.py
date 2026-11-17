from pathlib import Path
import os,socket,json,hashlib,tarfile
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
a=Path('/home/jovyan/bcsp_spcg_sixmodel_native_pending_20261117_v1.tar.gz');assert not a.is_symlink() and hashlib.sha256(a.read_bytes()).hexdigest()=='90182af9e43ee2053831f6bc9d52dcf8bf5bc978ac7b4231fc01e26a86fed5a4'
t=tarfile.open(a);assert all(x.isfile() for x in t.getmembers());qb=t.extractfile('payload/SPCG_sixmodel_native_execution_request_v1.json').read();assert hashlib.sha256(qb).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc'
q=json.loads(qb);m=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(m['remote_root']);idx=json.load(t.extractfile('payload/SPCG_sixmodel_input_index_v1.json'))
def exact(r):
 p=Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size==r['bytes'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 assert h.hexdigest()==r['sha256'] and (s.st_size,s.st_mtime_ns,s.st_ino)==(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ino),str(p)
for run in idx['runs']:exact(run['checkpoint'])
u={r['input']['path']:r['input'] for r in idx['inputs']};assert len(u)==210 and len(idx['runs'])==6 and len(idx['inputs'])==630
for r in u.values():exact(r)
print(json.dumps(dict(status='SIX_CHECKPOINTS_210_INPUTS_HASH_PASS',models=6,inputs=len(u))))
