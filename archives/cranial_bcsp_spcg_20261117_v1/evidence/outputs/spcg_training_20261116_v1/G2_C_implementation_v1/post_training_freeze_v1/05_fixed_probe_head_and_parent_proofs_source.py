from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G2C_training_20261116_v1');qp=r/'SPCG_G2_C_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
items={k:record(Path(q[k]['path'])) for k in ['probe_asset','head_initialization','mother_source','G0_C_freeze','G1_C_freeze']}
print(json.dumps(dict(records=items,free_bytes=os.statvfs(o).f_bavail*os.statvfs(o).f_frsize)))
