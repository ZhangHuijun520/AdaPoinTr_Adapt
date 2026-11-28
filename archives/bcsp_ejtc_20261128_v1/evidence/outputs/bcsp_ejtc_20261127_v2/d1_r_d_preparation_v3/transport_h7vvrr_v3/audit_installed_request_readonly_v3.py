from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent
e=d.parent/'post_installation_freeze_audit_v3';e.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
mp=d/'EJTC_R_D_h7vvrr_request_install_mapping_v3.json'
assert h(mp.read_bytes())=='a3fb20d398a264e87e631dfb2b751a1539bc76cb079f0d81aed88eda56a759fc'
m=json.loads(mp.read_bytes());f=m['files'][0]
local=(d.parent/f['member']).read_bytes();assert h(local)==m['request_sha256']
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path
assert socket.gethostname()=={m['identity']['hostname']!r} and os.getuid()==1000
def read(name):
 p=Path(name);a=p.lstat();assert stat.S_ISREG(a.st_mode) and p.resolve(strict=True)==p and a.st_size<=20971520
 b=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,len(b),hashlib.sha256(b).hexdigest()]
'''
def run(code,name):
 source=common+code;compile(source,'<post-install-readonly>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=m['identity']['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(cmd)<=2048
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','40','--',cmd],capture_output=True,timeout=55)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as w:json.dump(rec,w,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
absent=[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
inventory=f'''import subprocess
r=Path({m['existing_install_root']!r});assert r.resolve(strict=True)==r and r.is_dir()
rows=[read(str(p)) for p in sorted(r.iterdir())]
for p in {absent!r}:assert not os.path.lexists(p)
parent=Path({m['output_must_be_absent']!r}).parent;assert parent.resolve(strict=True)==parent and parent.is_dir()
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),rows=rows,new_paths_absent=True,session_absent=True)))
'''
first=run(inventory,'independent_inventory_before')
expected={x['path']:x['sha256'] for x in m['preserve_existing_files']};expected[f['target']]=f['sha256']
assert {x[0]:x[2] for x in first['rows']}==expected
assert next(x for x in first['rows'] if x[0]==f['target'])==[f['target'],f['bytes'],f['sha256']]
u=m['upload']
archive=f'''import tarfile,io
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.stat().st_size<=256 and s.read_text().split()==[row[2],p.name]
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 ts=a.getmembers();assert len(ts)==1 and ts[0].isfile() and ts[0].name=={f['member']!r}
 b=a.extractfile(ts[0]).read();member=[ts[0].name,len(b),hashlib.sha256(b).hexdigest()]
 assert member=={[f['member'],f['bytes'],f['sha256']]!r}
 assert b==Path({f['target']!r}).read_bytes()
print(json.dumps(dict(upload=row,member=member,archive_bytes_equal_installed=True)))
'''
run(archive,'independent_archive_and_installed_comparison')
assets=list(m['reused_assets'].values())
for i in range(0,len(assets),3):
 batch=assets[i:i+3]
 rows=run('print(json.dumps([read(p) for p in '+repr([x['path'] for x in batch])+']))','reused_bindings_'+str(i))
 assert rows==[[x['path'],x['bytes'],x['sha256']] for x in batch]
last=run(inventory,'independent_inventory_after');assert first==last
receipt=dict(status='FORMAL_READ_ONLY_V3_POST_INSTALLATION_FREEZE_AUDIT_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),installed_request_bytes=f['bytes'],exact_directory_files=len(expected),prior_failure_files_preserved=len(m['preserve_existing_files']),stable_before_after=True,archive_equal_installed=True,reused_assets_verified=len(assets),new_output_and_controls_absent=True,session_absent=True,remote_mutations=False,server_model_calls=0,training_authorized=False,training_started=False,evidence_sha256={p.name:h(p.read_bytes()) for p in sorted(e.glob('*.json'))})
with (e/'formal_post_installation_freeze_audit_v3.json').open('x',encoding='utf-8') as w:json.dump(receipt,w,indent=2)
print(json.dumps(receipt))
