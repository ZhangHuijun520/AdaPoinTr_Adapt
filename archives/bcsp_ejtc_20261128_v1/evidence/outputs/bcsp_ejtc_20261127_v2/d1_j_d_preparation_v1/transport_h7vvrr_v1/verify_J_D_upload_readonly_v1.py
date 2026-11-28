from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;e=d/'upload_readonly_v1';e.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
mp=d/'EJTC_J_D_h7vvrr_install_mapping_v1.json'
assert h(mp.read_bytes())=='b7e116a971c81e561c7db6afc5011329e71aabd1257cd281173698011a867163'
m=json.loads(mp.read_bytes());i=m['identity'];u=m['upload']
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path,PurePosixPath
assert socket.gethostname()=={i['hostname']!r} and os.getuid()=={i['uid']}
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=33554432
 raw=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,len(raw),hashlib.sha256(raw).hexdigest()]
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
receipt=dict(status='J_D_READ_ONLY_UPLOAD_VERIFICATION_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),hostname=archive['hostname'],uid=archive['uid'],upload_bytes=u['bytes'],upload_sha256=u['sha256'],archive_members=279,all_member_names_sizes_hashes_match=True,new_non_label_files=4,new_label_files=275,reused_labels_reverified=40,new_targets_absent=279,new_directories_absent=2,output_controls_and_session_absent=True,parents_valid=True,remote_mutations=False,installed=False,training_started=False,installation_and_training_require_separate_authorization=True)
with (e/'upload_readonly_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
