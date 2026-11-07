import hashlib,json,os,pathlib,socket,sys,tarfile
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');os.chdir(P)
assert pathlib.Path.cwd()==P and socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
seen={}
def exact(r):
 p=pathlib.Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.is_file() and p.stat().st_size==r['bytes'],str(p)
 if str(p) not in seen:seen[str(p)]=sha(p)
 assert seen[str(p)]==r['sha256'],str(p)
def read(r):exact(r);return json.loads(pathlib.Path(r['path']).read_bytes())
A=pathlib.Path('/home/jovyan/bcsp_p2_H1_foldC_pending_20261106_v1.tar.gz')
assert sha(A)=='b5b21992ae94283ee69f550bc2b1149f2c0bd89d5dbf204b8b074628831660fb'
with tarfile.open(A) as t:q=json.load(t.extractfile('payload/M_H1_foldC_seed0_training_execution_request_v1.json'))
I=q['identity'];assert str(pathlib.Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version']
for k,r in q['implementation'].items():
 if k not in ('entry','runtime'):exact(r)
for r in q['dependencies']:exact(r)
for k in ('numeric_policy','numeric_protocol','pair_contract','quantification_audit','quantification_request','initialization_reference','order_plan'):exact(q[k])
for k in ('qualified_receipt','verification','fold_binding'):exact(q['QC'][k])
for r in q['QC']['manifests'].values():exact(r)
scope=read(q['preflight_scope'])
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:exact(r)
for key,relkey in (('candidate','relative_target'),('isolated_model_project_sources','relative_path')):
 for r in scope['bindings'][key]:exact(dict(path=q['model_root']+'/'+r[relkey],bytes=r['bytes'],sha256=r['sha256']))
assert sha(pathlib.Path(q['model_root'])/'base_model.yaml')==scope['bindings']['base_config']['sha256']
fold=read(q['QC']['fold_binding'])['folds']['C'];ids=set(fold['train_case_ids']);assert len(ids)==315 and len(fold['train_sources'])==63
rows=[json.loads(s) for s in pathlib.Path(q['QC']['manifests']['8192']['path']).read_text().splitlines()]
selected=[r for r in rows if r['case_id'] in ids];assert len(selected)==315
for r in selected:
 rel=pathlib.PurePosixPath(r['point_path']);assert not rel.is_absolute() and '..' not in rel.parts
 p=pathlib.Path(q['data_root'])/str(rel);assert not any(x.is_symlink() for x in (p,*p.parents))
 assert p.is_file() and sha(p)==r['sha256'],str(p)
print(json.dumps(dict(status='READONLY_FROZEN_ASSETS_PASS',metadata_and_code_files=len(seen),train_NPZ_hashes=315,payload_deserialized=0,server_writes=0)),flush=True)
