from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G1C_training_20261116_v1');qp=r/'SPCG_G1_C_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
c=Path(q['launch_contract']['authorization_path']).parent;control={p.name:dict(**record(p),text=p.read_text()) for p in c.iterdir()};sources={k:record(Path(v['path'])) for k,v in q['implementation'].items()};installed={p.name:record(p) for p in r.iterdir() if p.is_file()}
expected=Path(q['order_plan']['path']);assert record(expected)['sha256']==q['order_plan']['sha256'];checks=dict(order_raw_bytes=(o/'order_plan.json').read_bytes()==expected.read_bytes())
print(json.dumps(dict(controls=control,sources=sources,installed=installed,checks=checks,initialization=read(o/'initialization.json'),construction=read(o/'model_construction.json'),optimizer=read(o/'optimizer_actual_defaults.json'),groups=read(o/'optimizer_parameter_groups.json'),exposure=read(o/'exposure.json'))))
