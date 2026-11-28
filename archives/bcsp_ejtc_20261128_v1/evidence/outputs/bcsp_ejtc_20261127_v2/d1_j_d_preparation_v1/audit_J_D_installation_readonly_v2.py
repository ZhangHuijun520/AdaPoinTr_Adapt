from pathlib import Path,PurePosixPath
import base64,datetime,hashlib,json,subprocess,zlib
b=Path(__file__).resolve().parent;t=b/'transport_h7vvrr_v1'
e=b/'post_installation_freeze_audit_v2';e.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
mp=t/'EJTC_J_D_h7vvrr_install_mapping_v1.json'
assert h(mp.read_bytes())=='b7e116a971c81e561c7db6afc5011329e71aabd1257cd281173698011a867163'
m=json.loads(mp.read_bytes());i=m['identity'];u=m['upload']
qp=b/'EJTC_D1_J_D_training_execution_request_h7vvrr_v1.json';q=json.loads(qp.read_bytes())
assert h(qp.read_bytes())==m['request_sha256']
common=f'''import os,socket,stat,json,hashlib
from pathlib import Path
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
 source=common+code;compile(source,'<J-installation-audit>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(cmd)<=2048
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--',cmd],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
absent=[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
inventory=f'''import subprocess
r=Path({m['new_install_root']!r});assert r.resolve(strict=True)==r and r.is_dir()
rows=[];directories=[]
for p in sorted(r.rglob('*')):
 assert p.resolve(strict=True)==p and not p.is_symlink()
 if p.is_dir():directories.append(str(p.relative_to(r)))
 else:rows.append(read(str(p)))
assert directories==['labels']
for name in {absent!r}:assert not os.path.lexists(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir()
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),rows=rows,directories=directories,output_and_controls_absent=True,session_absent=True)))
'''
before=run(inventory,'installed_inventory_before')
expected=sorted([[r['target'],r['bytes'],r['sha256']] for r in m['files']])
assert before['rows']==expected
archive=f'''import tarfile,io
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256
assert s.read_text().split()==[row[2],p.name]
members=[]
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 for item in a:
  parts=PurePosixPath(item.name).parts
  assert item.isfile() and not PurePosixPath(item.name).is_absolute() and '..' not in parts and item.name not in {{r[0] for r in members}} and len(members)<279
  assert len(parts)==1 or len(parts)==2 and parts[0]=='labels'
  raw=a.extractfile(item).read()
  assert raw==(Path({m['new_install_root']!r})/item.name).read_bytes()
  members.append([item.name,len(raw),hashlib.sha256(raw).hexdigest()])
print(json.dumps(dict(upload=row,members=sorted(members),archive_members_byte_equal_installed=True)))
'''
arch=run(archive,'archive_members_and_installed_bytes')
assert arch['members']==sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']])
assets={}
for k in ['initial_state','r_start']:assets[q['pairing'][k]['path']]=[q['pairing'][k]['bytes'],q['pairing'][k]['sha256']]
for k,r in q['files'].items():
 if k not in ('worker','label_table'):assets[r['path']]=[r['bytes'],r['sha256']]
r=q['binding']['interpreter'];assets[r['path']]=[r['bytes'],r['sha256']]
# The complete 464-file reuse set was rehashed immediately before installation.
# This independent post-install audit additionally rehashes critical pairing and source bindings.
paired=json.loads((b/'J_D_paired_contract_binding_v1.json').read_bytes())
order=paired['order'];assets[order['path']]=[order['bytes'],order['sha256']]
for rec in m['reused_label_files']:assets[rec['path']]=[rec['bytes'],rec['sha256']]
assert len(m['reused_label_files'])==40
paths=list(assets)
for j in range(0,len(paths),5):
 batch=paths[j:j+5]
 rows=run('print(json.dumps([read(p) for p in '+repr(batch)+']))','critical_reuse_'+str(j//5+1))
 assert rows==[[p,*assets[p]] for p in batch]
after=run(inventory,'installed_inventory_after');assert before==after
receipt=dict(status='FORMAL_READ_ONLY_J_D_POST_INSTALLATION_FREEZE_AUDIT_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),installed_files=279,installed_label_files=275,reused_label_files_verified=40,exact_subdirectory_count=1,exact_directory_inventory=True,all_installed_hashes_match=True,archive_members_byte_equal_installed=True,stable_before_after=True,critical_reused_bindings_independently_verified=len(assets),R_frozen_initial_and_start_evidence_unchanged=True,full_464_asset_recheck_scope='Performed at installation; this independent post-install audit verified critical source/pairing/order/interpreter bindings plus all 40 reused label files',output_and_controls_absent=True,session_absent=True,remote_mutations=False,model_calls=0,training_authorized=False,training_started=False,evidence_sha256={p.name:h(p.read_bytes()) for p in sorted(e.glob('*.json'))})
with (e/'formal_post_installation_freeze_audit_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
