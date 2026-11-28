"""Bounded read-only remote readiness. No remote writes, imports of CUDA or model execution."""
from pathlib import Path,PurePosixPath
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;base=d.parent
e=d/'server_readonly_h7vvrr_v1';e.mkdir(exist_ok=False)
load=lambda p:json.loads(p.read_bytes())
qpath=d/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v1.json';rid=hashlib.sha256(qpath.read_bytes()).hexdigest()
assert rid=='758f8297612a4c9b2253b88a4401df308002dd1426dd4edf48e0a2925500a5cb'
q=load(qpath);scope=load(d/'EJTC_RTJ_D_native315_scope_v1.json');i=q['binding']['identity']
common=f'''import os,socket,stat,hashlib,json,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
'''
def run(code,name):
 source=common+code;compile(source,'<Native315-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(command.encode())<=2048,len(command)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',command],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'),command_bytes=len(command.encode()))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
targets=[q['binding']['install_root'],q['binding']['output'],q['launch']['launcher']['path'],*[r['path'] for r in q['files'].values() if PurePosixPath(r['path']).is_relative_to(PurePosixPath(q['binding']['install_root']))],*[q['launch'][k] for k in ('request_path','authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path')]]
scan=f'''import subprocess
for name in {targets!r}:assert not os.path.lexists(name)
for name in {[q['binding']['install_root'],q['binding']['output']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
args=['/usr/bin/nvidia-smi','--id={i['gpu_uuid']}']
v=[x.strip() for x in subprocess.check_output(args+['--query-gpu=uuid,driver_version,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=8).strip().split(',')]
assert v[:4]=={[i['gpu_uuid'],i['driver_version'],i['gpu_name'],i['total_MiB']]!r}
assert int(v[4])<={q['binding']['resources']['idle_used_MiB']} and int(v[5])>={q['binding']['resources']['minimum_start_free_MiB']}
assert not subprocess.check_output(args+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
assert subprocess.run(['tmux','has-session','-t','='+{q['launch']['session_name']!r}],capture_output=True).returncode==1
s=os.statvfs(Path({q['binding']['install_root']!r}).parent);free=s.f_bavail*s.f_frsize
assert free>={q['launch']['matrix_disk_budget_bytes']}
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),gpu=v,disk_free_bytes=free,new_paths_absent=True,parents_valid=True,session_absent=True)))
'''
first=run(scan,'identity_resources_targets_before')
prior=load(base/'p1_cuda_preparation_v1/server_readonly_h7vvrr_v1/server_readiness_receipt_v1.json')
assets={p:r['expected'] for p,r in prior['files'].items() if 'training_input' not in r['groups']}
for rec in [q['binding']['interpreter'],*q['files'].values(),*q['checkpoints'].values()]:
 if not PurePosixPath(rec['path']).is_relative_to(PurePosixPath(q['binding']['install_root'])):assets[rec['path']]=[rec['bytes'],rec['sha256']]
for row in scope['inputs']:assets[row['input']['path']]=[row['input']['bytes'],row['input']['sha256']]
read='''def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
'''
paths=list(assets)
for j in range(0,len(paths),8):
 batch=paths[j:j+8];observed=run(read+'print(json.dumps([read(p) for p in '+repr(batch)+']))','asset_batch_'+str(j//8+1).zfill(2))
 assert observed==[[p,*assets[p]] for p in batch],'Frozen asset mismatch'
 print('Hashed '+str(min(j+8,len(paths)))+'/'+str(len(paths)),flush=True)
# Read only partial.npy from each already hash-verified NPZ, with stdlib NPY parsing.
partial='''import ast,io,struct,zipfile
def partial(name):
 with zipfile.ZipFile(name) as z:b=z.read('partial.npy')
 f=io.BytesIO(b);assert f.read(6)==b'\\x93NUMPY';v=f.read(2)
 n=struct.unpack('<H' if v==b'\\x01\\x00' else '<I',f.read(2 if v==b'\\x01\\x00' else 4))[0]
 a=ast.literal_eval(f.read(n).decode('latin1'));raw=f.read()
 assert a['shape']==(8192,3) and a['descr']=='<f4' and a['fortran_order'] is False and len(raw)==98304
 return [name,hashlib.sha256(raw).hexdigest()]
'''
for j in range(0,105,10):
 rows=scope['inputs'][j:j+10];names=[r['input']['path'] for r in rows]
 observed=run(partial+'print(json.dumps([partial(p) for p in '+repr(names)+']))','partial_batch_'+str(j//10+1).zfill(2))
 assert observed==[[r['input']['path'],r['partial_array_sha256']] for r in rows]
 print('Partial arrays '+str(min(j+10,105))+'/105',flush=True)
last=run(scan,'identity_resources_targets_after')
receipt=dict(status='EJTC_NATIVE315_READ_ONLY_SERVER_READINESS_PASS',request_sha256=rid,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),identity=i,gpu=last['gpu'],disk_free_bytes=last['disk_free_bytes'],verified_assets=len(assets),development_inputs=105,partial_array_hashes_verified=105,final_checkpoints_hashed=3,new_paths_absent=True,parents_valid=True,session_absent=True,remote_mutations=False,CUDA_imports=0,forward_calls=0,files=assets,scope='Snapshot only; installation and execution require separate authorizations')
with (e/'Native315_server_readiness_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))
