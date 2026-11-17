from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1D_training_20261117_v2');qp=r/'SPCG_G1_D_training_execution_request_v2.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
items={k:record(Path(q[k]['path'])) for k in ['probe_asset','head_initialization','mother_source','G0_D_freeze']}
print(json.dumps(items))
