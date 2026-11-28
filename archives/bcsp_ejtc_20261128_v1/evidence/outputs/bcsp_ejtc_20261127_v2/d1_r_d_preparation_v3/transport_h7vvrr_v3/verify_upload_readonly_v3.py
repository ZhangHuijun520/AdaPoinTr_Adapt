from pathlib import Path
import base64,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent
mp=d/'EJTC_R_D_h7vvrr_request_install_mapping_v3.json'
h=lambda b:hashlib.sha256(b).hexdigest()
assert h(mp.read_bytes())=='a3fb20d398a264e87e631dfb2b751a1539bc76cb079f0d81aed88eda56a759fc'
m=json.loads(mp.read_bytes())
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path
assert socket.gethostname()=={m['identity']['hostname']!r} and os.getuid()==1000
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode)
 assert a.st_size<=262144
 b=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,len(b),hashlib.sha256(b).hexdigest()]
'''
def run(code,name):
 source=common+code;compile(source,'<upload-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=m['identity']['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(cmd.encode())<=2048
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','40','--',cmd],capture_output=True,timeout=55)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (d/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
u=m['upload'];f=m['files'][0]
absent=[f['target'],m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
code=f'''import tarfile,io,subprocess
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256
assert s.read_text().split()==[row[2],p.name]
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 ts=a.getmembers();assert len(ts)==1 and ts[0].isfile() and ts[0].name=={f['member']!r}
 b=a.extractfile(ts[0]).read();member=[ts[0].name,len(b),hashlib.sha256(b).hexdigest()]
 assert member=={[f['member'],f['bytes'],f['sha256']]!r}
for name in {absent!r}:assert not os.path.lexists(name)
r=Path({m['existing_install_root']!r});assert r.resolve(strict=True)==r and r.is_dir()
o=Path({m['output_must_be_absent']!r}).parent;assert o.resolve(strict=True)==o and o.is_dir()
v=subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True)
assert v.returncode==1
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),upload=row,member=member,fresh_paths_absent=True,session_absent=True,parents_valid=True)))
'''
scan=run(code,'upload_member_and_fresh_paths_verification_v3')
preserved=[]
for i in range(0,len(m['preserve_existing_files']),5):
 batch=m['preserve_existing_files'][i:i+5]
 rows=run('print(json.dumps([read(p) for p in '+repr([x['path'] for x in batch])+']))','prior_failure_preservation_'+str(i))
 assert [[x[0],x[2]] for x in rows]==[[x['path'],x['sha256']] for x in batch]
 preserved.extend(rows)
receipt=dict(status='READ_ONLY_V3_UPLOAD_VERIFICATION_PASS',request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),identity=dict(hostname=scan['hostname'],uid=scan['uid']),upload_bytes=u['bytes'],upload_sha256=u['sha256'],archive_member_count=1,request_bytes=f['bytes'],member_sha256=f['sha256'],fresh_paths_absent=True,parents_valid=True,session_absent=True,prior_failure_files_preserved=len(preserved),remote_mutations=False,installed=False,training_started=False,installation_and_execution_require_separate_authorization=True)
with (d/'upload_readonly_verification_receipt_v3.json').open('x',encoding='utf-8') as w:json.dump(receipt,w,indent=2)
print(json.dumps(receipt))
