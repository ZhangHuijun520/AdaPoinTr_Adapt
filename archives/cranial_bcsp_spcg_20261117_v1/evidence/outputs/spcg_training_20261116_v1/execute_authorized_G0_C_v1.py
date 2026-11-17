"""Exact-request staged install and one tmux launch. Stops on any error; no retry."""
from pathlib import Path
import base64,zlib,json,subprocess,time
S=Path(__file__).resolve().parent;O=S/'authorized_execution_v1';O.mkdir()
QH='0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08'
PRE="""from pathlib import Path
import json,hashlib,tarfile,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
p=Path('/home/jovyan/adapointr_work/PoinTr');a=Path('/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz')
assert hashlib.sha256(a.read_bytes()).hexdigest()=='1e06b11d9c4d297f999dc64b0678174b16030f1c96dad57717cca351151c7462'
t=tarfile.open(a);qraw=t.extractfile('payload/SPCG_G0_C_training_execution_request_v1.json').read();assert hashlib.sha256(qraw).hexdigest()=='0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08'
q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=json.load(t.extractfile('installation_mapping_v1.json'));root=Path(mapping['remote_root'])
def exact(r):
 v=Path(r['path']);assert not any(x.is_symlink() for x in (v,*v.parents));assert v.stat().st_size==r['bytes'] and hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256'],str(v)
"""
def remote(label,body):
 code=PRE+body;b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
 args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c]
 assert len(subprocess.list2cmdline(args).encode())<=2048,('command length',label,len(subprocess.list2cmdline(args).encode()))
 (O/(label+'_source.py')).write_text(code,encoding='utf-8');r=subprocess.run(args,capture_output=True,timeout=65)
 (O/(label+'_stdout.bin')).write_bytes(r.stdout);(O/(label+'_stderr.bin')).write_bytes(r.stderr)
 (O/(label+'_exit.json')).write_text(json.dumps(dict(returncode=r.returncode)),encoding='utf-8')
 assert r.returncode==0,(label,r.returncode,r.stderr[-1000:]);v=json.loads(r.stdout);print(json.dumps(dict(phase=label,result=v)),flush=True);return v
remote('01_reused_assets',"""rows=[v for k,v in q['implementation'].items() if k not in ['entry','bridge']]+q['dependencies']+[q[k] for k in ['native_helper','preflight_scope','static_config','order_plan']]
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
""")
remote('02_targets_resources',"""import subprocess
assert not root.exists() and not root.is_symlink()
for v in [root,Path(q['output'])]:
 assert not v.exists() and not any(x.is_symlink() for x in (v,*v.parents));assert v.parent.is_dir()
for r in mapping['files']:
 assert not Path(r['target']).exists();b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
v=os.statvfs(p);assert v.f_bavail*v.f_frsize>=int(8.5*1024**3)
g=subprocess.run(['nvidia-smi','--query-gpu=uuid,driver_version,memory.used','--format=csv,noheader,nounits'],capture_output=True,timeout=10,check=True).stdout.decode().strip().split(',')
assert g[0].strip()==q['identity']['gpu_uuid'] and g[1].strip()==q['identity']['driver_version'] and int(g[2])<=256
print(json.dumps(dict(status='TARGETS_ABSENT_RESOURCES_PASS',free_bytes=v.f_bavail*v.f_frsize,GPU=g)))
""")
remote('03_install_once',"""assert not root.exists() and not root.is_symlink() and root.parent.is_dir()
for r in mapping['files']:
 assert Path(r['target']).parent==root and not Path(r['target']).exists();b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
assert not any(x.is_symlink() for x in root.parents)
root.mkdir(mode=0o700)
for r in mapping['files']:
 with Path(r['target']).open('xb') as f:f.write(t.extractfile(r['member']).read())
for r in mapping['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
print(json.dumps(dict(status='INSTALLED_9_EXCLUSIVE_HASH_PASS',files=len(mapping['files']))))
""")
remote('04_materialize_launch_once',"""import importlib.util,subprocess
for r in mapping['files']:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
assert not Path(q['output']).exists();L=q['launch_contract'];control=Path(L['authorization_path']).parent;assert not control.exists()
sp=importlib.util.spec_from_file_location('authorized_spcg_entry',q['implementation']['entry']['path']);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
qh=hashlib.sha256(qraw).hexdigest();auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='User authorized exactG0_C request3900step execution2026-11-16')
ab=(json.dumps(auth,indent=2)+'\n').encode();rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=hashlib.sha256(ab).hexdigest());rb=(json.dumps(rt,indent=2)+'\n').encode()
e.validate(q,qh,auth,hashlib.sha256(ab).hexdigest(),rt)
script=e.render_launcher(q,qh,hashlib.sha256(ab).hexdigest(),hashlib.sha256(rb).hexdigest()).encode()
assert not control.parent.exists() and not any(x.is_symlink() for x in control.parents)
control.parent.mkdir(mode=0o700);control.mkdir(mode=0o700)
for name,b in [(L['authorization_path'],ab),(L['runtime_path'],rb),(L['launcher_path'],script)]:
 with Path(name).open('xb') as f:f.write(b)
with Path(L['launch_attempt_path']).open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),f)
v=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'/bin/bash',L['launcher_path']],capture_output=True,timeout=10)
print(json.dumps(dict(status='SINGLE_TMUX_ATTEMPT',returncode=v.returncode,stderr=v.stderr.decode(errors='replace'),session=L['tmux_session'],output=q['output'])))
assert v.returncode==0
""")
