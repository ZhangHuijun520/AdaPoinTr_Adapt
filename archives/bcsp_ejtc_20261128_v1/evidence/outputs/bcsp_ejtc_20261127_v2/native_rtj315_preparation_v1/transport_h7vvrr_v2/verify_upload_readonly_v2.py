"""Read-only uploaded package and seven-member verification; no installation."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;e=d/'upload_readonly_v1';e.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
mp=d/'EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json'
assert h(mp.read_bytes())=='cc91eb9573e0221c6ab4df567eb0857073bf697c93e11d0514d73dd7ad9d48eb'
m=json.loads(mp.read_bytes());i=m['identity'];u=m['upload']
common=f'''import os,socket,stat,json,hashlib,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
def read(name,limit):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=limit
 raw=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return raw
'''
def run(code,name):
 source=common+code;compile(source,'<Native315-upload-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(command.encode())<=2048,len(command)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','40','--',command],capture_output=True,timeout=55)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'),command_bytes=len(command.encode()))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
archive=run(f'''import io,tarfile
p=Path({u['path']!r});raw=read(str(p),1048576)
assert len(raw)=={u['bytes']} and hashlib.sha256(raw).hexdigest()=={u['sha256']!r}
check=read({m['upload_checksum_path']!r},256)
assert check.decode('ascii').split()==[{u['sha256']!r},p.name]
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:
 rows=[]
 for t in a:
  assert t.isfile() and t.name not in ('.','..') and '/' not in t.name and '\\\\' not in t.name and 0<t.size<=262144 and len(rows)<7
  b=a.extractfile(t).read();assert len(b)==t.size
  rows.append([t.name,len(b),hashlib.sha256(b).hexdigest()])
assert len(rows)==len(set(r[0] for r in rows))==7
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),upload_sha256=hashlib.sha256(raw).hexdigest(),members=rows,checksum_sha256=hashlib.sha256(check).hexdigest())))
''','archive_and_members')
assert sorted(archive['members'])==sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']])
absent=[m['new_install_root'],m['output_must_be_absent']]+[r['target'] for r in m['files']]+m['runtime_controls_must_be_absent']
paths=run(f'''import subprocess
for name in {absent!r}:assert not os.path.lexists(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(new_paths_absent=True,parents_valid=True,session_absent=True)))
''','new_target_paths')
receipt=dict(status='EJTC_NATIVE315_V2_READ_ONLY_UPLOAD_VERIFICATION_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),hostname=archive['hostname'],uid=archive['uid'],upload_bytes=u['bytes'],upload_sha256=u['sha256'],member_count=7,all_member_hashes_match=True,checksum_matches=True,**paths,remote_mutations=False,installed=False,forward_calls=0,
 scope='Uploaded package and new targets only; all 167 reused assets, 105 partial arrays and current GPU/resources must be reverified before any authorized installation',installation_and_execution_require_separate_authorization=True)
with (e/'upload_readonly_receipt_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
