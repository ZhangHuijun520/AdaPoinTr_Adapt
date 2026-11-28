from pathlib import Path
import base64,zlib,hashlib,json,subprocess
b=Path('outputs/bcsp_ejtc_20261127_v2/d1_t_d_preparation_v1');d=b/'transport_h7vvrr_v1';e=d/'upload_readonly_v1';e.mkdir(exist_ok=False)
mp=d/'EJTC_T_D_h7vvrr_install_mapping_v1.json';h=lambda raw:hashlib.sha256(raw).hexdigest();assert h(mp.read_bytes())=='ce0eef8385aa206e20ae723f094103d9e79c093c3a3387e4e3c1161c824eebbe'
m=json.loads(mp.read_bytes());q=json.loads((b/'EJTC_D1_T_D_training_execution_request_h7vvrr_v1.json').read_bytes());i=m['identity'];u=m['upload']
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path
assert socket.gethostname()=={i['hostname']!r} and os.getuid()=={i['uid']}
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=20971520
 raw=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,len(raw),hashlib.sha256(raw).hexdigest()]
'''
def run(code,name):
 source=common+code;compile(source,'<T-upload-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"';assert len(cmd)<=2048,len(cmd)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','40','--',cmd],capture_output=True,timeout=55)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
expected=sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']])
code=f'''import tarfile,io
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256
assert s.read_text().split()==[row[2],p.name]
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 rows=[]
 for t in a:
  assert t.isfile() and '/' not in t.name and len(rows)<3
  raw=a.extractfile(t).read();rows.append([t.name,len(raw),hashlib.sha256(raw).hexdigest()])
assert sorted(rows)=={expected!r}
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),upload=row,members=rows)))
'''
archive=run(code,'archive_and_members')
absent=[m['new_install_root'],m['output_must_be_absent']]+[r['target'] for r in m['files']]+m['runtime_controls_must_be_absent']
code=f'''import subprocess
for name in {absent!r}:assert not os.path.lexists(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(new_paths_absent=True,parents_valid=True,session_absent=True)))
'''
paths=run(code,'new_target_paths')
# Verify the small R start evidence used by T without re-running any model.
rstart=q['pairing']['r_start'];rrow=run('print(json.dumps(read('+repr(rstart['path'])+')))','R_start_evidence')
assert rrow==[rstart['path'],rstart['bytes'],rstart['sha256']]
receipt=dict(status='T_D_READ_ONLY_UPLOAD_VERIFICATION_PASS',request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),hostname=archive['hostname'],uid=archive['uid'],upload_bytes=u['bytes'],upload_sha256=u['sha256'],member_count=3,members_match=True,**paths,R_start_evidence_unchanged=True,remote_mutations=False,installed=False,training_started=False,installation_and_training_require_separate_authorization=True)
with (e/'upload_readonly_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
