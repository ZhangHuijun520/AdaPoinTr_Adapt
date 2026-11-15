"""Adapt proven short-call controller to exact S-ref_C training request."""
from pathlib import Path
R=Path(__file__).resolve().parent.parent
S=R/'local_tools'
src=(S/'execute_scq_rf_cuda_once_v1.py').read_text(encoding='utf-8')
changes=[('scq_rf_cuda_preparation_20261114_v1','scq_rf_Sref_C_training_implementation_20261114_v1'),
('85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32','6d63c000de45f02cee7e7318abedaef0bb96b39e32a5e0ae6f40bdfbf2c67b21'),
('SCQ_RF_artificial_cuda_execution_request_v1.json','SCQ_RF_Sref_C_training_execution_request_v1.json'),
("len(mp['files'])==12","len(mp['files'])==15"),('bcsp_scq_rf_cuda_admission_v1.py','bcsp_scq_rf_Sref_C_training_entry_v1.py'),
('bcsp-scq-rf-cuda-authorization-v1','bcsp-scq-rf-training-authorization-v1'),('bcsp-scq-rf-cuda-runtime-v1','bcsp-scq-rf-training-runtime-v1'),
('len(lines)==len(expected)==13','len(lines)==len(expected)==16'),('len(ms)==13 and len({m.name for m in ms})==13','len(ms)==16 and len({m.name for m in ms})==16'),
('members=13','members=16'),('len(rows)==12','len(rows)==15'),('TWELVE_FILES_EXCLUSIVE_INSTALL_PASS','FIFTEEN_FILES_EXCLUSIVE_INSTALL_PASS'),('files=12','files=15')]
for a,b in changes:
 assert a in src,a
 src=src.replace(a,b)
src=src.replace("I=q['identity'];L=q['launch_contract'];", "I=q['identity'];L=dict(q['launch_contract'],launch_attempt_path=q['launch_attempt']);")
src=src.replace('entry.authorize(q,RH,auth,ah,runtime)','assert runtime[\'request_sha256\']==auth[\'request_sha256\']==RH and runtime[\'authorization_sha256\']==ah')
old="""q=bound(REQUEST,REQUESTSHA);m.authorize(q,REQUESTSHA,bound(AUTH,AUTHSHA),AUTHSHA,bound(RUNTIME,RUNTIMESHA))
assert q['science']['full_forward']==5 and q['science']['full_loss']==q['science']['full_backward']==4"""
new="""def record(path,digest):return dict(path=path,bytes=Path(path).stat().st_size,sha256=digest)
result=m.authorize(record(REQUEST,REQUESTSHA),record(AUTH,AUTHSHA),record(RUNTIME,RUNTIMESHA))
assert len(result[3])==315 and result[1]['counts']['updates']==3900"""
assert old in src;src=src.replace(old,new)
src=src.replace("forwards=5,losses=4,backwards=4,optimizer_steps=0", "arm='S-ref',fold='C',updates_cap=3900,planned_exposures=31200")
src=src.replace('SINGLE_RF_CUDA_TMUX_SUBMITTED','SINGLE_RF_SREF_C_TRAINING_SUBMITTED').replace('SINGLE_RF_CUDA_ATTEMPT_SUBMITTED','SINGLE_RF_SREF_C_TRAINING_ATTEMPT_SUBMITTED')
anchor="add('exclusive_install','''"
extra="""add('train315_hashes','''from pathlib import Path,PurePosixPath
import socket,hashlib,json
assert socket.gethostname()==HOST
def bound(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];return p
fold=json.loads(bound(FOLD).read_bytes())['folds']['C'];ids=fold['train_case_ids'];assert len(ids)==len(set(ids))==315
rows={r['case_id']:r for r in [json.loads(l) for l in bound(MANIFEST).read_text().splitlines()]}
root=Path(ROOT);total=0
for cid in ids:
 r=rows[cid];relative=PurePosixPath(r['point_path']);assert not relative.is_absolute() and '..' not in relative.parts and r['source_id'] in fold['train_sources']
 p=root/r['point_path'];assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
 before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk);total+=len(chunk)
 after=p.stat();assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert h.hexdigest()==r['sha256'],str(p)
print(json.dumps(dict(status='TRAIN315_EXACT_HASHES_PASS',files=315,sources=63,hashed_bytes=total,array_reads=0)))
''',dict(HOST=I['hostname'],FOLD=q['QC']['fold_binding'],MANIFEST=q['QC']['manifests']['8192'],ROOT=q['data_root']))
"""
assert anchor in src;src=src.replace(anchor,extra+anchor)
target=S/'execute_rf_Sref_C_training_once_v1.py';compile(src,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
print('TRAINING_CONTROLLER_ADAPTED_NOT_EXECUTED')
