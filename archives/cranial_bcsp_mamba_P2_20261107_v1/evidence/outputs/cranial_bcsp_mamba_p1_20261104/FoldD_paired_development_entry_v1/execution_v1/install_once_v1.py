SIDE=[{'path': '/home/jovyan/bcsp_p1_foldD_paired_development_transport_v1.tar.gz.sha256', 'bytes': 119, 'sha256': '6064ed75d910f836406a5f5af30265348c14961621752a1fc30fb745afdf555d'}, {'path': '/home/jovyan/bcsp_p1_foldD_paired_development_transport_v1.tar.gz.bytes', 'bytes': 6, 'sha256': '3af16600a6c71a5740a70c5d75d12c89d5494fb874006a0ba66c8d879618869f'}, {'path': '/home/jovyan/bcsp_p1_foldD_paired_development_transport_v1.tar.gz.contents.sha256', 'bytes': 1022, 'sha256': 'd628189b63bc02089865cb65c32bfcef422332adf2ca412b6562a394717e0705'}]
MEMBERS=[{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/bcsp_p1_foldD_paired_predict_v1.py', 'bytes': 22321, 'sha256': 'a4ce1f45c5cba3a52ee93aceefa222f6b2b89a61d32015f003cc8ace2fe9afcd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/CPU_contract_result_v1.json', 'bytes': 511, 'sha256': '85dc1d8a1d982a3ce54d469f32cf0b94ecc8fd2bf178f73dde1b044c4cbf51be'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/FoldD_T0_M0_development_execution_request_v1.json', 'bytes': 12677, 'sha256': '763d780df7352d945011fbdcc4e4800bfaa1d97fd031d4fae92bde5bbb48875c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/launch_once_template_v1.sh', 'bytes': 2433, 'sha256': '432bfe40bea0616d5affb41e5a04826d34e63d12fc9e5a9f1ec7b677acb19595'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/local_P3_v1.json', 'bytes': 3295, 'sha256': 'daaa63f2f7fd01e96be48e5fef691fca7add93b4ac77a1ba6a3e49a6e805e292'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/M0_post_training_and_pair_freeze_audit_v1.json', 'bytes': 59133, 'sha256': 'f65c3dd7d82814f705a09f11f5fa95f2583fba71380cdd29cd8b9f4f59e5bb61'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/paired_development_input_index_v1.json', 'bytes': 169241, 'sha256': 'c89bae1bce82f1e6927306acb9c494de232aeb4a784737882bcc92c47cc82104'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/paired_development_protocol_v1.json', 'bytes': 3176, 'sha256': '3e4b47cf5d14df30e73ac6c85a33cc26de4ee1b61e09c18c891cb32ee09fecf0'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/paired_FoldD_training_freeze_receipt_v1.json', 'bytes': 1540, 'sha256': 'ea2b474399e9663769002c141747b2276bb6e33005adf1fd59c463149ef3317d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_paired_development_20261106_v1/T0_post_training_freeze_audit_v1.json', 'bytes': 212760, 'sha256': '02bd553e42f10098e16fd863c6716d664019735e705c20b3941b2b81d5672877'}]
import os,json,socket,hashlib,tarfile,subprocess,shutil,time
from pathlib import Path
start=time.monotonic()
def check(v,t):
 if not v:raise RuntimeError(t)
def clean(p):
 p=Path(p);check(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),"link/path "+str(p));return p
def sha(p):
 h=hashlib.sha256()
 with clean(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def exact(r):
 p=clean(r['path']);check(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'identity '+str(p));return p
project=clean('/home/jovyan/adapointr_work/PoinTr');os.chdir(project)
check(socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000,'container identity')
print(json.dumps(dict(phase='identity',hostname=socket.gethostname(),uid=os.getuid(),cwd=os.getcwd())),flush=True)
a=exact(dict(path='/home/jovyan/bcsp_p1_foldD_paired_development_transport_v1.tar.gz',bytes=65094,sha256='516b91e59658ebf98abaa2b691e143055ad6463cbbb28098b1888360d2366139'))
for r in SIDE:exact(r)
with tarfile.open(a) as t:
 ms=t.getmembers();check(len(ms)==10 and len({x.name for x in ms})==10 and all(x.isfile() and Path(x.name).name==x.name for x in ms),'archive members')
 payload={m.name:t.extractfile(m).read() for m in ms}
raw=payload['FoldD_T0_M0_development_execution_request_v1.json'];check(hashlib.sha256(raw).hexdigest()=='763d780df7352d945011fbdcc4e4800bfaa1d97fd031d4fae92bde5bbb48875c','request SHA')
q=json.loads(raw);root=clean(q['entry']['path']).parent
check(q['schema']=='bcsp-p1-foldD-paired-development-prediction-v1' and q['fold']=='D' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['forward_budget']==210,'D request scope')
check(set(payload)=={Path(r['path']).name for r in MEMBERS},'exact package set')
for r in MEMBERS:
 data=payload[Path(r['path']).name];check(len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'exact package member')

check(not root.exists() and not clean(q['output']).exists(),'new install/output already exists')
for name in payload:check(not clean(root/name).exists(),'target exists')
for key in ['static_config','preflight_scope','numeric_policy','fold_binding','source_index','source_manifest','helper']:exact(q[key])
for r in list(q['implementation'].values())+q['dependencies']:exact(r)
scope=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:exact(r)
sources={r['relative_target']:r for r in scope['bindings']['candidate']}
for r in scope['bindings']['isolated_model_project_sources']:
 check(r['relative_path'] not in sources,'source duplicate');sources[r['relative_path']]=r
check(len(sources)==18,'finite18 project sources')
for rel,r in sources.items():exact(dict(path=str(clean(Path(q['model_root'])/rel)),bytes=r['bytes'],sha256=r['sha256']))
check(sha(Path(q['model_root'])/'base_model.yaml')==scope['bindings']['base_config']['sha256'],'base model config')
index=json.loads(payload['paired_development_input_index_v1.json'])
fold=json.loads(Path(q['fold_binding']['path']).read_bytes())['folds']['D']
check([r['label'] for r in index['runs']]==['D_T0','D_M0'] and len(index['inputs'])==210,'twoD arms')
check(all(r['fold']=='D' and r['dev_case_ids']==fold['dev_case_ids'] and r['train_sources']==fold['train_sources'] for r in index['runs']),'frozen D cohort')
check(all([r['case_id'] for r in index['inputs'] if r['run']==run['label']]==fold['dev_case_ids'] for run in index['runs']),'ordered105each')
for key in ('T0','M0'):
 audit=json.loads(payload[Path(q['training_audits'][key]['path']).name]);check(all(audit['checks'].values()),'training freeze checks')
 check(audit['checkpoint']['sha256']==next(r for r in index['runs'] if r['variant']==key)['checkpoint']['sha256'],'checkpoint audit binding')

for r in index['runs']:exact(r['checkpoint'])
unique={r['input']['path']:r['input'] for r in index['inputs']};check(len(unique)==105,'input count')
for r in unique.values():exact(r)
print(json.dumps(dict(phase='assets',upload_sha256=sha(a),members=10,checkpoints=2,unique_inputs=105,inputs_hashed_without_array_loading=True)),flush=True)
I=q['identity'];gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().splitlines();check(len(gpu)==1,'single GPU');g=[x.strip() for x in gpu[0].split(',')]
check(g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256,'GPU identity/idle')
check(str(Path(os.sys.executable).resolve())==I['python_realpath'] and os.sys.version.split()[0]==I['python_version'],'Python identity')
check(shutil.disk_usage(project).free>=q['limits']['minimum_free_disk_bytes'],'disk')
print(json.dumps(dict(status='READ_ONLY_INSTALLATION_READINESS_PASS',gpu=g,free_disk_bytes=shutil.disk_usage(project).free,new_root=str(root),seconds=time.monotonic()-start)),flush=True)

# All read-only guards above run again immediately before exclusive installation.
for record in [q['entry'],q['input_index'],q['protocol'],q['pair_receipt'],q['P3'],q['launch_contract']['launcher_template'],*q['training_audits'].values()]:
 data=payload[Path(record['path']).name]
 check(len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'],'payload binding')
check(not root.exists() and not clean(q['output']).exists(),'fresh roots before write')
check(root.parent.is_dir() and not root.parent.is_symlink(),'install parent')
root.mkdir(mode=0o700)
for name,data in payload.items():
 target=clean(root/name)
 with target.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 target.chmod(0o600);check(sha(target)==hashlib.sha256(data).hexdigest(),'installed hash')
(root/'control').mkdir(mode=0o700)
print(json.dumps(dict(status='EXCLUSIVE_INSTALL_10_FILES_PASS',root=str(root),installed=[dict(name=name,bytes=len(data),sha256=sha(root/name)) for name,data in payload.items()],GPU_calls=0)),flush=True)
