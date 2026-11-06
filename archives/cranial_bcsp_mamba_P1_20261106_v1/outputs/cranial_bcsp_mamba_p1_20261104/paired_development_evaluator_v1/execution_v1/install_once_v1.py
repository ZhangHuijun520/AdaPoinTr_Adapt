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
a=exact(dict(path='/home/jovyan/bcsp_p1_foldC_paired_development_transport_v1.tar.gz',bytes=52128,sha256='cf125586d868d0c9c95f3cef8e8c616150f164888da5263877302a158322ba14'))
with tarfile.open(a) as t:
 ms=t.getmembers();check(len(ms)==9 and len({x.name for x in ms})==9 and all(x.isfile() and Path(x.name).name==x.name for x in ms),'archive members')
 payload={m.name:t.extractfile(m).read() for m in ms}
raw=payload['FoldC_T0_M0_development_execution_request_v1.json'];check(hashlib.sha256(raw).hexdigest()=='d4e5665e7c285f0d8246e6ca3b104d6f003afd4faf35683e8170aa9ec8215418','request SHA')
q=json.loads(raw);root=clean(q['entry']['path']).parent
check(not root.exists() and not clean(q['output']).exists(),'new install/output already exists')
for name in payload:check(not clean(root/name).exists(),'target exists')
for key in ['static_config','preflight_scope','numeric_policy','fold_binding','source_index','source_manifest','helper']:exact(q[key])
for r in list(q['implementation'].values())+q['dependencies']:exact(r)
scope=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:exact(r)
index=json.loads(payload['paired_development_input_index_v1.json'])
for r in index['runs']:exact(r['checkpoint'])
unique={r['input']['path']:r['input'] for r in index['inputs']};check(len(unique)==105,'input count')
for r in unique.values():exact(r)
print(json.dumps(dict(phase='assets',upload_sha256=sha(a),members=9,checkpoints=2,unique_inputs=105,inputs_hashed_without_array_loading=True)),flush=True)
I=q['identity'];gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().splitlines();check(len(gpu)==1,'single GPU');g=[x.strip() for x in gpu[0].split(',')]
check(g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256,'GPU identity/idle')
check(str(Path(os.sys.executable).resolve())==I['python_realpath'] and os.sys.version.split()[0]==I['python_version'],'Python identity')
check(shutil.disk_usage(project).free>=q['limits']['minimum_free_disk_bytes'],'disk')
print(json.dumps(dict(status='READ_ONLY_INSTALLATION_READINESS_PASS',gpu=g,free_disk_bytes=shutil.disk_usage(project).free,new_root=str(root),seconds=time.monotonic()-start)),flush=True)

# All read-only guards above run again immediately before exclusive installation.
for record in [q['entry'],q['input_index'],q['protocol'],q['pair_receipt'],q['P3'],q['launch_contract']['launcher_template'],*q['training_audits'].values()]:
 data=payload[Path(record['path']).name]
 check(len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'],'payload binding')
root.mkdir(mode=0o700)
for name,data in payload.items():
 target=clean(root/name)
 with target.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 target.chmod(0o600);check(sha(target)==hashlib.sha256(data).hexdigest(),'installed hash')
(root/'control').mkdir(mode=0o700)
print(json.dumps(dict(status='EXCLUSIVE_INSTALL_9_FILES_PASS',root=str(root),installed=[dict(name=name,bytes=len(data),sha256=sha(root/name)) for name,data in payload.items()],GPU_calls=0)),flush=True)
