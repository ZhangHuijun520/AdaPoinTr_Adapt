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
g0=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G0_foldC_seed0_train_20261116_v3')
pair=read(Path(q['G0_C_freeze']['path'])) if 'G0_C_freeze' in q else None
m0=[json.loads(l) for l in (g0/'metrics.jsonl').read_text().splitlines()];m1=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()]
print(json.dumps(dict(order_identical=(g0/'order_plan.json').read_bytes()==(o/'order_plan.json').read_bytes(),exposure_identical=read(g0/'exposure.json')==read(o/'exposure.json'),initialization_G0=read(g0/'initialization.json'),pair_rows=len(m0)==len(m1)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm']) for a,b in zip(m0,m1)),G0_log_records={n:record(g0/n) for n in ['metrics.jsonl','initialization.json','order_plan.json','exposure.json']},construction=read(o/'model_construction.json'))))
