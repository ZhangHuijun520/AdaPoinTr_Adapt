"""One authorized no-overwrite seven-file install, after all frozen preconditions."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;b=d.parent;e=d/'installation_evidence_v1';e.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
mp=d/'EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json';assert h(mp.read_bytes())=='cc91eb9573e0221c6ab4df567eb0857073bf697c93e11d0514d73dd7ad9d48eb'
m=json.loads(mp.read_bytes());q=json.loads((b/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes());scope=json.loads((b/'EJTC_RTJ_D_native315_scope_v2.json').read_bytes())
assert h((b/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes())==m['request_sha256']
i=m['identity'];u=m['upload'];assets=m['reused_assets'];assert len(assets)==167
common=f'''import os,socket,stat,json,hashlib,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
'''
def render(code):
 source=common+code;compile(source,'<Native315-authorized-install>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(command.encode())<=2048,len(command)
 return command
def run(code,name):
 command=render(code)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',command],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'),command_bytes=len(command.encode()))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
absent=[m['new_install_root'],m['output_must_be_absent']]+[r['target'] for r in m['files']]+m['runtime_controls_must_be_absent']
pathcheck=f'''import subprocess
for name in {absent!r}:assert not os.path.lexists(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
'''
resource=f'''args=['/usr/bin/nvidia-smi','--id={i['gpu_uuid']}']
v=[x.strip() for x in subprocess.check_output(args+['--query-gpu=uuid,driver_version,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=8).strip().split(',')]
assert v[:4]=={[i['gpu_uuid'],i['driver_version'],i['gpu_name'],i['total_MiB']]!r}
assert int(v[4])<={m['resources']['idle_used_MiB']} and int(v[5])>={m['resources']['minimum_start_free_MiB']}
assert not subprocess.check_output(args+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
s=os.statvfs(Path({m['new_install_root']!r}).parent);free=s.f_bavail*s.f_frsize;assert free>={m['matrix_disk_budget_bytes']}
'''
scan=pathcheck+resource+'print(json.dumps(dict(gpu=v,disk_free_bytes=free,all_targets_absent=True,parents_valid=True,session_absent=True)))'
read='''def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
'''
expected=sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']]);fingerprint=h(json.dumps(expected,separators=(',',':')).encode())
package=f'''import tarfile,io
p=Path({u['path']!r});a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size=={u['bytes']}
raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=={u['sha256']!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256 and s.read_text().split()==[{u['sha256']!r},p.name]
data={{}}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for t in archive:
  assert t.isfile() and '/' not in t.name and '\\\\' not in t.name and t.name not in ('.','..') and t.name not in data and len(data)<7 and 0<t.size<=262144
  data[t.name]=archive.extractfile(t).read();assert len(data[t.name])==t.size
def sig(data):return hashlib.sha256(json.dumps(sorted([k,len(v),hashlib.sha256(v).hexdigest()] for k,v in data.items()),separators=(',',':')).encode()).hexdigest()
assert len(data)==7 and sig(data)=={fingerprint!r}
'''
install=pathcheck+package+f'''r=Path({m['new_install_root']!r});r.mkdir()
for name,raw in data.items():
 with (r/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
new={{p.name:p.read_bytes() for p in r.iterdir() if p.is_file() and not p.is_symlink()}}
assert len(list(r.iterdir()))==7 and sig(new)=={fingerprint!r}
assert all(not os.path.lexists(p) for p in {[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']!r})
print(json.dumps(dict(installed=7,created_directories=1,readback_fingerprint=sig(new),output_and_controls_absent=True)))
'''
partial='''import ast,io,struct,zipfile
def partial(name):
 with zipfile.ZipFile(name) as z:b=z.read('partial.npy')
 f=io.BytesIO(b);assert f.read(6)==b'\\x93NUMPY';v=f.read(2);assert v in (b'\\x01\\x00',b'\\x02\\x00')
 n=struct.unpack('<H' if v[0]==1 else '<I',f.read(2 if v[0]==1 else 4))[0]
 a=ast.literal_eval(f.read(n).decode('latin1'));raw=f.read()
 assert a==dict(descr='<f4',fortran_order=False,shape=(8192,3)) and len(raw)==98304
 return [name,hashlib.sha256(raw).hexdigest()]
'''
jobs=[]
paths=list(assets)
for j in range(0,len(paths),8):
 batch=paths[j:j+8];jobs.append((read+'print(json.dumps([read(p) for p in '+repr(batch)+']))','reuse_'+str(j//8+1).zfill(2),[[p,assets[p]['bytes'],assets[p]['sha256']] for p in batch]))
for j in range(0,105,10):
 rows=scope['inputs'][j:j+10];names=[r['input']['path'] for r in rows]
 jobs.append((partial+'print(json.dumps([partial(p) for p in '+repr(names)+']))','partial_'+str(j//10+1).zfill(2),[[r['input']['path'],r['partial_array_sha256']] for r in rows]))
# Compile and enforce short-call budgets for every call before the first remote operation.
for code in [scan,package+'print(json.dumps(dict(members=7,fingerprint=sig(data))))',install,*[j[0] for j in jobs]]:render(code)
run(scan,'identity_resources_targets_before')
run(package+'print(json.dumps(dict(members=7,fingerprint=sig(data))))','upload_reverification')
for j,(code,name,expected_rows) in enumerate(jobs):
 assert run(code,name)==expected_rows,'Frozen asset/partial mismatch'
 print('Verified read-only batch '+str(j+1)+'/'+str(len(jobs)),flush=True)
last_resources=run(scan,'identity_resources_targets_immediately_before')
result=run(install,'exclusive_install_and_immediate_readback')
assert result['installed']==7 and result['readback_fingerprint']==fingerprint
receipt=dict(status='EJTC_NATIVE315_V2_NO_OVERWRITE_INSTALL_AND_IMMEDIATE_READBACK_PASS',request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),installed_files=7,created_directories=1,reused_files_hashed=167,partial_array_hashes_verified=105,all_installed_hashes_match=True,result=result,resources_immediately_before=last_resources,CUDA_imports=0,forward_calls=0,execution_authorized=False,formal_post_installation_audit_performed=False,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
with (e/'installation_receipt_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
