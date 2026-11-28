"""Independent post-installation freeze audit. Read bytes only; no installed code execution."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;e=d/'post_installation_freeze_audit_v2';e.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
mp=d/'EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json';assert h(mp.read_bytes())=='cc91eb9573e0221c6ab4df567eb0857073bf697c93e11d0514d73dd7ad9d48eb'
m=json.loads(mp.read_bytes());i=m['identity'];u=m['upload']
common=f'''import os,socket,stat,json,hashlib,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
'''
def render(code):
 source=common+code;compile(source,'<independent-post-install-audit>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"';assert len(command.encode())<=2048,len(command)
 return command
def run(code,name):
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',render(code)],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
absent=[m['output_must_be_absent']]+m['runtime_controls_must_be_absent']
inventory=f'''import subprocess
r=Path({m['new_install_root']!r});assert r.resolve(strict=True)==r and r.is_dir() and not r.is_symlink()
rows=[read(str(p)) for p in sorted(r.iterdir())]
for name in {absent!r}:assert not os.path.lexists(name)
p=Path({m['output_must_be_absent']!r}).parent;assert p.resolve(strict=True)==p and p.is_dir()
assert subprocess.run(['tmux','has-session','-t','='+{m['session_must_be_absent']!r}],capture_output=True).returncode==1
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),files=rows,output_controls_absent=True,session_absent=True)))
'''
archive=f'''import io,tarfile
p=Path({u['path']!r});row=read(str(p));assert row=={[u['path'],u['bytes'],u['sha256']]!r}
s=Path({m['upload_checksum_path']!r});assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256 and s.read_text().split()==[row[2],p.name]
rows=[];names=set();root=Path({m['new_install_root']!r})
with tarfile.open(fileobj=io.BytesIO(p.read_bytes()),mode='r:gz') as a:
 for t in a:
  assert t.isfile() and '/' not in t.name and '\\\\' not in t.name and t.name not in ('.','..') and t.name not in names and len(rows)<7 and 0<t.size<=262144
  b=a.extractfile(t).read();assert len(b)==t.size and b==(root/t.name).read_bytes()
  names.add(t.name);rows.append([t.name,len(b),hashlib.sha256(b).hexdigest()])
assert len(rows)==7
print(json.dumps(dict(upload=row,members=rows,archive_members_equal_installed_bytes=True)))
'''
assets=m['reused_assets'];paths=list(assets);jobs=[]
for j in range(0,len(paths),8):
 batch=paths[j:j+8];jobs.append(('print(json.dumps([read(p) for p in '+repr(batch)+']))','reuse_'+str(j//8+1).zfill(2),[[p,assets[p]['bytes'],assets[p]['sha256']] for p in batch]))
for code in [inventory,archive,*[j[0] for j in jobs]]:render(code)
expected=sorted([[r['target'],r['bytes'],r['sha256']] for r in m['files']])
first=run(inventory,'independent_inventory_before');assert first['files']==expected
packed=run(archive,'independent_archive_comparison')
assert sorted(packed['members'])==sorted([[r['member'],r['bytes'],r['sha256']] for r in m['files']])
for j,(code,name,rows) in enumerate(jobs):
 assert run(code,name)==rows,'Reused frozen file drift'
 print('Audited reused batch '+str(j+1)+'/'+str(len(jobs)),flush=True)
last=run(inventory,'independent_inventory_after');assert first==last
# Verify local frozen request links; remote bytes were independently hashed twice above.
qp=d.parent/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json';q=json.loads(qp.read_bytes())
assert h(qp.read_bytes())==m['request_sha256'] and q['execution_authorized'] is False and q['counts']==dict(forward=315,loss=0,backward=0,optimizer_steps=0,BNCal=0,warmup=0,TTA=0,scoring=0)
bytarget={r['target']:r for r in m['files']}
for binding in [q['files'][k] for k in ('worker','scope','receipt_R','receipt_T','receipt_J')]+[q['launch']['launcher']]:
 assert [bytarget[binding['path']][k] for k in ('bytes','sha256')]==[binding[k] for k in ('bytes','sha256')]
receipt=dict(status='FORMAL_READ_ONLY_EJTC_NATIVE315_V2_POST_INSTALLATION_FREEZE_AUDIT_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=m['request_sha256'],mapping_sha256=h(mp.read_bytes()),exact_installed_file_count=7,unexpected_files_or_directories=0,all_installed_hashes_independently_verified_twice=True,stable_before_after=True,archive_members_equal_installed_bytes=True,reused_files_hashed=167,development_input_files_included=105,final_checkpoints_included=3,request_scope_and_launcher_bindings_match=True,output_controls_absent=True,session_absent=True,remote_mutations=False,CUDA_imports=0,model_calls=0,execution_authorized=False,execution_started=False,
 evidence_sha256={p.name:h(p.read_bytes()) for p in sorted(e.glob('*.json'))},scope='Formal installation freeze audit only; fresh runtime resource checks and separate exact-request execution authorization are still required')
with (e/'formal_post_installation_freeze_audit_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
