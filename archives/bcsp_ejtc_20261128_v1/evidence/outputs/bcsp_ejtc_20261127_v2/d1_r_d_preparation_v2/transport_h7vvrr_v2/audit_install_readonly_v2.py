from pathlib import Path
import base64,hashlib,json,subprocess,zlib,datetime
d=Path(__file__).resolve().parent
out=d.parent/'post_installation_freeze_audit_v2'
out.mkdir(exist_ok=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,value):
 with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
mp=d/'EJTC_R_D_h7vvrr_install_mapping_v2.json'
assert sha(mp.read_bytes())=='51eeea477e197946e6671a7e6c127a3817d69311a93025cc267e8b756d989c9d'
m=json.loads(mp.read_bytes())
qpath=d.parent/'EJTC_D1_R_D_training_execution_request_h7vvrr_v2.json'
assert sha(qpath.read_bytes())==m['request_sha256']
q=json.loads(qpath.read_bytes())
common='''import os,socket,hashlib,json,stat
from pathlib import Path
assert socket.gethostname()==%r and os.getuid()==1000
def read(name):
 p=Path(name);a=p.lstat()
 assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode)
 b=p.read_bytes();z=p.lstat()
 assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,len(b),hashlib.sha256(b).hexdigest()]
'''%m['identity']['hostname']
def run(code,name):
 source=common+code
 compile(source,'<post-install-readonly>','exec')
 b=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=m['identity']['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+b+'\')))"'
 assert len(command.encode())<=2048
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','55','--',command],capture_output=True,timeout=65)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 save(name+'.json',rec)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
root=m['new_install_root']
absent=[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
inventory=f'''r=Path({root!r})
assert r.resolve(strict=True)==r and r.is_dir()
names=sorted(p.name for p in r.iterdir())
assert names=={sorted(x['member'] for x in m['files'])!r}
for p in {absent!r}:assert not os.path.lexists(p)
print(json.dumps(dict(names=names,rows=[read(str(p)) for p in sorted(r.iterdir())],absent={absent!r})))
'''
first=run(inventory,'independent_installed_inventory_before')
expected=sorted([[x['target'],x['bytes'],x['sha256']] for x in m['files']])
assert first['rows']==expected
u=m['upload']
code=f'''import tarfile,io
p=Path({u['path']!r});row=read(str(p));b=p.read_bytes()
assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path(str(p)+'.sha256');assert s.resolve(strict=True)==s and s.stat().st_size<=256
assert s.read_text().split()==[row[2],p.name]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as a:
 rows=[]
 for t in a:
  assert t.isfile() and '/' not in t.name and len(rows)<4
  x=a.extractfile(t).read();rows.append([t.name,len(x),hashlib.sha256(x).hexdigest()])
print(json.dumps(dict(upload=row,members=sorted(rows))))
'''
upload=run(code,'independent_upload_members')
assert upload['members']==sorted([[x['member'],x['bytes'],x['sha256']] for x in m['files']])
assets=list(m['reused_assets'].values())+[m['interpreter']]
parent=json.loads((Path.cwd()/'outputs/bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json').read_bytes())
assets.append(parent['order'])
for i in range(0,len(assets),3):
 batch=assets[i:i+3]
 rows=run('print(json.dumps([read(p) for p in '+repr([x['path'] for x in batch])+']))','reused_bindings_'+str(i))
 assert rows==[[x['path'],x['bytes'],x['sha256']] for x in batch]
last=run(inventory,'independent_installed_inventory_after')
assert last==first
receipt=dict(status='FORMAL_READ_ONLY_POST_INSTALLATION_FREEZE_AUDIT_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=sha(mp.read_bytes()),installed_files=4,exact_inventory=True,installed_sha256_match=True,upload_members_match=True,stable_before_after=True,reused_bindings_verified=len(assets),output_and_controls_absent=True,remote_mutations=False,model_calls=0,training_authorized=False,training_started=False,evidence={p.name:sha(p.read_bytes()) for p in sorted(out.glob('*.json'))})
save('formal_post_installation_freeze_audit_v2.json',receipt)
print(json.dumps(receipt,ensure_ascii=False))
