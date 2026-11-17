from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0D_training_20261116_v1');qp=r/'SPCG_G0_D_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
qc=q['QC'];records={k:record(Path(qc[k]['path'])) for k in ['qualified_receipt','verification','fold_binding']};records.update({'manifest_'+k:record(Path(v['path'])) for k,v in qc['manifests'].items()})
fold=read(Path(qc['fold_binding']['path']))['folds']['D'];plan=read(o/'order_plan.json');M=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()];proofs={k:dict(record=record(Path(v['path'])),value=read(Path(v['path']))) for k,v in q['C_matrix_freezes'].items()}
print(json.dumps(dict(records=records,proofs=proofs,D_selected_order=plan['case_ids']==fold['train_case_ids'],D_counts=len(fold['train_case_ids'])==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21,D_train_only=all(set(m['case_ids'])<=set(fold['train_case_ids']) and set(m['source_ids'])<=set(fold['train_sources']) for m in M),D_disjoint=not set(fold['train_sources'])&set(fold['dev_sources']))))
