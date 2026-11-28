from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;e=d/'installation_evidence_v1';e.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
mp=d/'EJTC_J_D_h7vvrr_install_mapping_v1.json'
assert h(mp.read_bytes())=='b7e116a971c81e561c7db6afc5011329e71aabd1257cd281173698011a867163'
m=json.loads(mp.read_bytes());i=m['identity'];u=m['upload']
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path,PurePosixPath
assert socket.gethostname()=={i['hostname']!r} and os.getuid()=={i['uid']}
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 value=hashlib.sha256()
 with p.open('rb') as f:
  for raw in iter(lambda:f.read(4194304),b''):value.update(raw)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,value.hexdigest()]
'''
def run(code,name):
 source=common+code;compile(source,'<J-upload-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(cmd)<=2048,len(cmd)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',cmd],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
expected=sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']])
fingerprint=h(json.dumps(expected,separators=(',',':')).encode())
code=f'''import io,tarfile
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256
assert s.read_text().split()==[row[2],p.name]
rows=[];seen=set()
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 for t in a:
  parts=PurePosixPath(t.name).parts
  assert t.isfile() and not PurePosixPath(t.name).is_absolute() and '..' not in parts and '\\\\' not in t.name
  assert len(parts)==1 or len(parts)==2 and parts[0]=='labels'
  assert t.name not in seen and len(rows)<279 and t.size<=262144
  raw=a.extractfile(t).read();assert len(raw)==t.size
  rows.append([t.name,len(raw),hashlib.sha256(raw).hexdigest()]);seen.add(t.name)
assert len(rows)==279 and hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest()=={fingerprint!r}
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),upload=row,members=sorted(rows))))
'''
archive=run(code,'archive_members_and_hashes')
assert archive['members']==expected
targets=[r['target'] for r in m['files']]
absent=m['directories_to_create']+[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
code=f'''import subprocess
for name in {absent!r}:assert not os.path.lexists(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(new_directories_absent=True,output_controls_absent=True,parents_valid=True,session_absent=True)))
'''
paths=run(code,'new_roots_and_controls')
for j in range(0,len(targets),25):
 batch=targets[j:j+25]
 r=run('paths='+repr(batch)+"\nfor p in paths:assert not os.path.lexists(p) and all(not x.is_symlink() for x in (Path(p),*Path(p).parents))\nprint(json.dumps(dict(absent=paths)))",'target_absence_'+str(j//25+1).zfill(2))
 assert r['absent']==batch
reuse=m['reused_label_files'];assert len(reuse)==40
for j in range(0,len(reuse),10):
 batch=reuse[j:j+10]
 rows=run('print(json.dumps([read(p) for p in '+repr([r['path'] for r in batch])+']))','reused_labels_'+str(j//10+1))
 assert rows==[[r['path'],r['bytes'],r['sha256']] for r in batch]

assets=m['reused_assets'];asset_paths=list(assets)
for j in range(0,len(asset_paths),10):
 batch=asset_paths[j:j+10]
 rows=run('print(json.dumps([read(p) for p in '+repr(batch)+']))','all_reused_assets_'+str(j//10+1).zfill(2))
 assert rows==[[p,assets[p]['bytes'],assets[p]['sha256']] for p in batch]
 print('Verified '+str(min(j+10,len(asset_paths)))+'/'+str(len(asset_paths)),flush=True)
q=json.loads((d.parent/'EJTC_D1_J_D_training_execution_request_h7vvrr_v1.json').read_bytes())
resource_code=f'''import subprocess
args=['/usr/bin/nvidia-smi','--id={i['gpu_uuid']}']
v=[s.strip() for s in subprocess.check_output(args+['--query-gpu=uuid,driver_version,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=8).strip().split(',')]
assert v[:2]=={[i['gpu_uuid'],i['driver_version']]!r} and int(v[2])<={q['binding']['resources']['idle_used_MiB']} and int(v[3])>={q['binding']['resources']['minimum_start_free_MiB']}
assert not subprocess.check_output(args+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
s=os.statvfs(Path({m['new_install_root']!r}).parent);free=s.f_bavail*s.f_frsize
assert free>={q['launch']['matrix_disk_budget_bytes']}
print(json.dumps(dict(gpu=v,disk_free_bytes=free)))
'''
resources=run(resource_code,'resources_before_install')
install=f'''import tarfile,io,subprocess
r=Path({m['new_install_root']!r});o=Path({m['output_must_be_absent']!r})
for name in {absent!r}:assert not os.path.lexists(name)
for t in (r,o):assert t.parent.resolve(strict=True)==t.parent and t.parent.is_dir() and os.access(t.parent,os.W_OK|os.X_OK)
p=Path({u['path']!r});assert read(str(p))=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.stat().st_size<=256 and s.read_text().split()==[{u['sha256']!r},p.name]
data={{}}
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 for t in a:
  parts=PurePosixPath(t.name).parts
  assert t.isfile() and not PurePosixPath(t.name).is_absolute() and '..' not in parts and '\\\\' not in t.name
  assert len(parts)==1 or len(parts)==2 and parts[0]=='labels'
  assert t.name not in data and len(data)<279 and t.size<=262144
  data[t.name]=a.extractfile(t).read();assert len(data[t.name])==t.size
  assert not os.path.lexists(r/t.name)
def sig(data):return hashlib.sha256(json.dumps(sorted([k,len(v),hashlib.sha256(v).hexdigest()] for k,v in data.items()),separators=(',',':')).encode()).hexdigest()
assert len(data)==279 and sig(data)=={fingerprint!r}
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
r.mkdir();(r/'labels').mkdir()
for name,raw in data.items():
 p=r/name;assert p.parent.resolve(strict=True)==p.parent
 with p.open('xb') as w:w.write(raw)
new={{str(p.relative_to(r)):p.read_bytes() for p in r.rglob('*') if p.is_file()}}
assert len(new)==279 and sig(new)=={fingerprint!r}
assert [str(p.relative_to(r)) for p in r.rglob('*') if p.is_dir()]==['labels']
assert all(not os.path.lexists(p) for p in {[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']!r})
print(json.dumps(dict(installed=279,created_directories=2,readback_fingerprint=sig(new),output_and_controls_absent=True)))
'''
result=run(install,'exclusive_install_and_immediate_readback')
assert result['installed']==279 and result['readback_fingerprint']==fingerprint
receipt=dict(status='J_D_NO_OVERWRITE_INSTALL_AND_IMMEDIATE_READBACK_PASS',request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),installed_files=279,created_directories=2,reused_assets_verified=len(assets),reused_label_files_verified=40,training_inputs=315,resources=resources,all_installed_hashes_match=True,output_and_controls_absent=True,training_authorized=False,training_started=False,model_calls=0,formal_post_installation_audit_performed=False)
with (e/'installation_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
