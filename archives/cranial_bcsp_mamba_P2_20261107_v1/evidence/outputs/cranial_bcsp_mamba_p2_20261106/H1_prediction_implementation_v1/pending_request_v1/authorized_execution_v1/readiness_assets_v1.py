import hashlib,json,os,pathlib,socket,sys,tarfile
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');os.chdir(P)
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
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
A=pathlib.Path('/home/jovyan/bcsp_p2_H1_twofold_prediction_pending_20261106_v1.tar.gz')
assert sha(A)=='00eab49474bd23d4d0139dc1e74078e61b5c2a5b4678b081c0d4c53aa891fe9b'
with tarfile.open(A) as t:
 q=json.load(t.extractfile('payload/H1_C_D_development_execution_request_v1.json'))
 index=json.load(t.extractfile('payload/H1_C_D_input_index_v1.json'))
I=q['identity'];assert str(pathlib.Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version']
for r in list(q['implementation'].values())+q['dependencies']:exact(r)
for k in ('static_config','numeric_policy','helper','source_index','source_manifest','fold_binding'):exact(q[k])
scope=read(q['preflight_scope'])
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:exact(r)
for key,relkey in (('candidate','relative_target'),('isolated_model_project_sources','relative_path')):
 for r in scope['bindings'][key]:exact(dict(path=q['model_root']+'/'+r[relkey],bytes=r['bytes'],sha256=r['sha256']))
assert sha(pathlib.Path(q['model_root'])/'base_model.yaml')==scope['bindings']['base_config']['sha256']
folds=read(q['fold_binding'])['folds'];assert len(index['inputs'])==210 and len(index['runs'])==2
for run in index['runs']:
 f=run['fold'];exact(run['checkpoint']);rows=[r for r in index['inputs'] if r['fold']==f]
 assert len(rows)==105 and [r['case_id'] for r in rows]==folds[f]['dev_case_ids']
 assert set(run['train_sources']).isdisjoint(run['dev_sources'])
 for row in rows:exact(row['input'])
print(json.dumps(dict(status='READONLY_TWO_H1_WEIGHTS_210_INPUTS_ASSETS_PASS',exact_files=len(seen),checkpoint_files=2,dev_input_files=210,payload_deserialized=0,server_writes=0)),flush=True)
