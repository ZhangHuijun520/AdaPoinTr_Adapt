SIDE=[{'path': '/home/jovyan/bcsp_p1_T0_foldD_seed0_training_20261106_v1.tar.gz.sha256', 'bytes': 118, 'sha256': 'e84bd9be64e5f3e2ffbdd8cb379dc09e5f9497d2f16ec239bb52c6a5892e9d14'}, {'path': '/home/jovyan/bcsp_p1_T0_foldD_seed0_training_20261106_v1.tar.gz.bytes', 'bytes': 7, 'sha256': '1ff827ea84fe406c4adc68cc4a44b0e8140d1fc2701d2a0508d85adc5e99d161'}, {'path': '/home/jovyan/bcsp_p1_T0_foldD_seed0_training_20261106_v1.tar.gz.contents.sha256', 'bytes': 607, 'sha256': '57edf62eaea0d611e43cdabc21ee93882ae0ea4b5c59977d0a060784f03fff23'}]
import os,json,socket,hashlib,tarfile,subprocess,shutil,time
from pathlib import Path
start=time.monotonic();read_bytes=0
def need(v,t):
 if not v:raise RuntimeError(t)
def clean(p):
 p=Path(p);need(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/path '+str(p));return p
def sha(p):
 global read_bytes
 h=hashlib.sha256()
 with clean(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   read_bytes+=len(b);need(read_bytes<=2147483648 and time.monotonic()-start<=60,'read/time budget');h.update(b)
 return h.hexdigest()
def exact(r):
 p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'file identity '+str(p));return p
qh='6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82'
need(socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000,'current container');os.chdir('/home/jovyan/adapointr_work/PoinTr')
a=exact(dict(path='/home/jovyan/bcsp_p1_T0_foldD_seed0_training_20261106_v1.tar.gz',bytes=17698,sha256='32d4cba38aec92075eaaab4e4f068fbbb9caeb18160f69ec39730bd1a1f818e3'))
for r in SIDE:exact(r)
with tarfile.open(a) as t:
 members=t.getmembers();need(len(members)==len({m.name for m in members})==6 and all(m.isfile() and Path(m.name).name==m.name and m.size<1048576 for m in members),'six regular package members');payload={m.name:t.extractfile(m).read() for m in members}
raw=payload['T0_foldD_seed0_training_execution_request_v1.json'];need(hashlib.sha256(raw).hexdigest()==qh,'request SHA');q=json.loads(raw);I=q['identity'];L=q['launch_contract'];root=clean(q['implementation']['entry']['path']).parent
need(q['schema']=='bcsp-p1-foldD-training-request-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['fold']=='D' and q['variant']=='T0' and q['t0_pairing'] is None,'T0_D only')
need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(os.sys.executable).resolve())==I['python_realpath'] and os.sys.version.split()[0]==I['python_version'],'identity/Python')
need(not root.exists() and not clean(q['output']).exists(),'fresh install/output')
for name in payload:need(not clean(root/name).exists(),'target exists '+name)
for r in [q['implementation']['entry'],q['pair_contract'],L['launcher_template']]:
 data=payload[Path(r['path']).name];need(len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'package bound file')
need(hashlib.sha256(payload['implementation_P3_v1.json']).hexdigest()==q['provenance']['implementation_P3_sha256'] and hashlib.sha256(payload['CPU_contract_result_v1.json']).hexdigest()==q['provenance']['CPU_contract_result_sha256'],'P3/CPU result')
need(json.loads(payload['CPU_contract_result_v1.json'])['count']==62 and json.loads(payload['implementation_P3_v1.json'])['status']=='PASS_FOR_PENDING_T0_D_REQUEST_ONLY','CPU/P3 status')
for r in [q['static_config'],q['order_plan'],q['preflight_scope'],q['numeric_policy'],q['numeric_protocol'],q['quantification_audit'],q['quantification_request'],q['initialization_reference'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*[r for k,r in q['implementation'].items() if k!='entry'],*q['dependencies']]:exact(r)
scope=json.loads(Path(q['preflight_scope']['path']).read_bytes());sources={r['relative_target']:r for r in scope['bindings']['candidate']}
for r in scope['bindings']['isolated_model_project_sources']:need(r['relative_path'] not in sources,'duplicate source');sources[r['relative_path']]=r
need(len(sources)==18,'finite18 model sources')
for rel,r in sources.items():exact(dict(path=str(clean(Path(q['model_root'])/rel)),bytes=r['bytes'],sha256=r['sha256']))
need(sha(Path(q['model_root'])/'base_model.yaml')==scope['bindings']['base_config']['sha256'],'base config')
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:exact(r)
fold=json.loads(Path(q['QC']['fold_binding']['path']).read_bytes())['folds']['D'];manifest={r['case_id']:r for r in [json.loads(x) for x in Path(q['QC']['manifests']['8192']['path']).read_text().splitlines()]}
need(len(fold['train_case_ids'])==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21 and not set(fold['train_sources'])&set(fold['dev_sources']),'D source/fold')
for cid in fold['train_case_ids']:
 r=manifest[cid];p=clean(Path(q['data_root'])/r['point_path']);need(r['source_id'] in fold['train_sources'],'training allowlist');exact(dict(path=str(p),bytes=p.stat().st_size,sha256=r['sha256']))
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().splitlines();need(len(gpu)==1,'one GPU');g=[x.strip() for x in gpu[0].split(',')]
need(g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256,'GPU identity/idle');need(shutil.disk_usage(I['project']).free>=4294967296,'free disk')
print(json.dumps(dict(status='T0_D_UPLOAD_ASSETS_AND_INSTALLATION_READINESS_PASS',GPU=g,training_files=315,finite_model_sources=18,free_disk_bytes=shutil.disk_usage(I['project']).free,read_bytes=read_bytes,seconds=time.monotonic()-start)),flush=True)
root.mkdir(mode=0o700)
installed=[]
for name,data in payload.items():
 p=clean(root/name)
 with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 p.chmod(0o600);h=sha(p);need(h==hashlib.sha256(data).hexdigest(),'installed identity');installed.append(dict(path=str(p),bytes=len(data),sha256=h))
(root/'control').mkdir(mode=0o700)
print(json.dumps(dict(status='T0_D_EXCLUSIVE_INSTALL_6_FILES_PASS',installed=installed,request_sha256=qh,model_calls=0,GPU_calls=0)),flush=True)
