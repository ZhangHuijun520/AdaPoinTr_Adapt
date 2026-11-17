from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='c5993b324c3fcd735bdcd64df1c4ccadfa36de97476a7326dc3788eac15cc3c3'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G2_C_training_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
rows=[v for k,v in q['implementation'].items() if k not in ['entry','bridge']]+q['dependencies']+[q[k] for k in ['native_helper','preflight_scope','static_config','order_plan','probe_asset','head_initialization','mother_source']]
qc=q['QC'];rows += [qc['qualified_receipt'],qc['verification'],qc['fold_binding']]+list(qc['manifests'].values())
for r in rows:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in s['bindings']['provider']+s['bindings']['environment_metadata']:exact(r)
sources=[dict(path=str(Path(q['model_root'])/r.get('relative_target',r.get('relative_path'))),bytes=r['bytes'],sha256=r['sha256']) for r in s['bindings']['candidate']+s['bindings']['isolated_model_project_sources']]
for r in sources:exact(r)
fold=json.loads(Path(qc['fold_binding']['path']).read_bytes())['folds']['C'];records=[json.loads(l) for l in Path(qc['manifests']['8192']['path']).read_text().splitlines()];selected=[r for r in records if r['case_id'] in fold['train_case_ids']];assert len(selected)==315
for r in selected:
 rel=Path(r['point_path']);assert not rel.is_absolute() and '..' not in rel.parts;v=Path(q['data_root'])/rel;assert not any(x.is_symlink() for x in (v,*v.parents));assert hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256']
print(json.dumps(dict(status='REUSED_ASSETS_AND315_TRAIN_HASHES_PASS',sources=len(sources),reused=len(rows),train_inputs=len(selected))))
