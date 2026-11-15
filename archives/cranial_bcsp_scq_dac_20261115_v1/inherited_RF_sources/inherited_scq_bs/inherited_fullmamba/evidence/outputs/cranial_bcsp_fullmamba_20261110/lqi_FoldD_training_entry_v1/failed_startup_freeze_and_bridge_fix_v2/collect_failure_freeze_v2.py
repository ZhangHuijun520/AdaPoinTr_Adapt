import base64,hashlib,json,shlex,subprocess,zlib
from pathlib import Path
F=Path(__file__).resolve().parent
CODE=r'''
import pathlib,hashlib,json,os,socket,base64,subprocess,shutil
P=pathlib.Path;assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
roots=[P('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v1'),P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v1')];rows=[];dirs=[];total=0
for role,root in enumerate(roots):
 assert not any(p.is_symlink() for p in (root,*root.parents))
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_dir():dirs.append([role,str(p.relative_to(root))]);continue
  assert p.is_file() and p.suffix not in ('.pth','.npz','.npy');b=p.read_bytes();total+=len(b);assert total<8388608
  st=p.stat();r=dict(role=role,name=str(p.relative_to(root)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),fingerprint=[st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode])
  if CONTENT:r['base64']=base64.b64encode(b).decode()
  rows.append(r)
assert len(rows)==28 and (roots[0]/'exit_code.txt').read_text().strip()=='1'
assert not P('/proc/'+(roots[0]/'worker.pid').read_text().strip()).exists() and subprocess.run(['tmux','has-session','-t','bcsp_lqi_foldD_train_20261111_v1'],capture_output=True,timeout=5).returncode==1
new=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2');out=roots[0].with_name('LQI_foldD_seed0_train_20261111_v2')
assert all(not p.exists() and not any(x.is_symlink() for x in (p,*p.parents)) for p in (new,out))
print(json.dumps(dict(status='FAILED_STARTUP_READONLY_FREEZE_PASS',rows=rows,dirs=dirs,free_disk=shutil.disk_usage(roots[0]).free,new_targets_absent=True,worker_tmux_absent=True,server_writes=0)))
'''
for label,content in [('before',True),('after',False)]:
 src='CONTENT='+repr(content)+'\n'+CODE;blob=base64.b64encode(zlib.compress(src.encode(),9)).decode();wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(blob)+')),"<failure-freeze>","exec"))';cmd=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',wrapper]);assert len(cmd.encode())<=2048
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','25','--',cmd],capture_output=True,timeout=35)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert r.returncode==0,(r.returncode,r.stdout[-1500:]);v=json.loads(r.stdout)
 if content:
  for row in v['rows']:
   p=F/'downloads'/('output' if row['role']==0 else 'installed')/row['name'];p.parent.mkdir(parents=True,exist_ok=True);b=base64.b64decode(row.pop('base64'));assert hashlib.sha256(b).hexdigest()==row['sha256']
   with p.open('xb') as f:f.write(b)
 with (F/(label+'_result.json')).open('x') as f:json.dump(v,f,indent=2)
 print(json.dumps(dict(phase=label,status=v['status'],files=len(v['rows']))),flush=True)
a=json.loads((F/'before_result.json').read_bytes());b=json.loads((F/'after_result.json').read_bytes());assert a['rows']==b['rows'] and a['dirs']==b['dirs']
out=F/'downloads/output';assert set(p.name for p in out.iterdir())=={'launch.log','worker.pid','exit_code.txt','startup_failure.json','tmp'} if (out/'tmp').exists() else set(p.name for p in out.iterdir())=={'launch.log','worker.pid','exit_code.txt','startup_failure.json'}
failure=json.loads((out/'startup_failure.json').read_bytes());assert 'bcsp_lqi_runtime_adapter_v1.py' in failure['error']
with (F/'failure_freeze_audit_result_v2.json').open('x') as f:json.dump(dict(status='FORMAL_LQI_D_FAILED_STARTUP_FREEZE_PASS',files=28,stable_content_fingerprints=True,exit_code=1,no_metrics_or_checkpoint=True,worker_tmux_absent=True,model_forward=0,optimizer_steps=0,basis='Bound source failed at bridge import before model dispatch; no train artifacts',server_writes=0,new_targets_absent=True),f,indent=2)
