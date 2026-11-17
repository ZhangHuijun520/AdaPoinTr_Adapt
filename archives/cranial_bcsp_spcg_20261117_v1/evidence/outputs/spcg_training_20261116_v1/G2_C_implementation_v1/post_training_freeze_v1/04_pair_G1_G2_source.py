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
g1=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldC_seed0_train_20261116_v1')
m1=[json.loads(l) for l in (g1/'metrics.jsonl').read_text().splitlines()];m2=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()]
print(json.dumps(dict(order_identical=(g1/'order_plan.json').read_bytes()==(o/'order_plan.json').read_bytes(),exposure_identical=read(g1/'exposure.json')==read(o/'exposure.json'),initialization=read(g1/'initialization.json'),optimizer=read(g1/'optimizer_actual_defaults.json'),groups=read(g1/'optimizer_parameter_groups.json'),pair_rows=len(m1)==len(m2)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm']) for a,b in zip(m1,m2)),parent_records={n:record(g1/n) for n in ['metrics.jsonl','initialization.json','order_plan.json','exposure.json','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json']},construction=read(g1/'model_construction.json'))))
