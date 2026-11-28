from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent
out=d.parent/'failed_authorization_freeze_v2';out.mkdir(exist_ok=False)
qraw=(d.parent/'EJTC_D1_R_D_training_execution_request_h7vvrr_v2.json').read_bytes()
h=lambda b:hashlib.sha256(b).hexdigest()
rid='5bb56b3e3dfeaa47edb54d0d0ccedba0075ba90a21b5f0ca8beb22fedbb275cd'
assert h(qraw)==rid
q=json.loads(qraw);m=json.loads((d/'EJTC_R_D_h7vvrr_install_mapping_v2.json').read_bytes())
code=f'''import os,socket,json,hashlib,base64,stat,subprocess
from pathlib import Path
assert socket.gethostname()=={q['binding']['identity']['hostname']!r} and os.getuid()==1000
r=Path({m['new_install_root']!r});o=Path({m['output_must_be_absent']!r})
assert r.resolve(strict=True)==r
rows=[]
for p in sorted(r.iterdir()):
 a=p.lstat();assert stat.S_ISREG(a.st_mode) and p.resolve(strict=True)==p and a.st_size<=100000
 b=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 rows.append([p.name,len(b),hashlib.sha256(b).hexdigest(),base64.b64encode(b).decode()])
live=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:c=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode('utf-8','replace')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if str(r) in c:live.append([int(p.name),c])
v=subprocess.run(['tmux','has-session','-t','=bcsp_ejtc_r_d_h7vvrr_v2'],capture_output=True)
assert v.returncode in (0,1)
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),files=rows,output_absent=not os.path.lexists(o),session_absent=v.returncode==1,live=live)))
'''
compile(code,'<read-only-failed-audit>','exec')
blob=base64.b64encode(zlib.compress(code.encode(),9)).decode()
command=q['binding']['identity']['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
assert len(command)<=2048
def collect(n):
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',command],capture_output=True,timeout=45)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 (out/(n+'.json')).write_text(json.dumps(rec,indent=2),encoding='utf-8')
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
a=collect('independent_before');b=collect('independent_after');assert a==b
files={r[0]:base64.b64decode(r[3]) for r in a['files']}
expected={x['member'] for x in m['files']}|{'R_D_authorization_v1.json','R_D_runtime_v1.json','R_D_dispatch_v1.log','R_D_single_attempt_v1.log','R_D_resource_v1.jsonl','R_D_exit_code.txt'}
assert set(files)==expected
for x in m['files']:assert len(files[x['member']])==x['bytes'] and h(files[x['member']])==x['sha256']
assert a['output_absent'] and a['session_absent'] and not a['live']
auth=json.loads(files['R_D_authorization_v1.json']);rt=json.loads(files['R_D_runtime_v1.json'])
assert auth==json.loads((d.parent/'R_D_user_execution_authorization_v2.json').read_bytes())
assert auth['request_sha256']==rid and rid not in auth['user_authorization_text']
assert rt==dict(schema='bcsp-development-runtime-v1',request_sha256=rid,authorization_sha256=h(files['R_D_authorization_v1.json']))
assert files['R_D_exit_code.txt'].strip()==b'1'
assert b'ValueError: single use authorization chain' in files['R_D_single_attempt_v1.log']
resources=[json.loads(x) for x in files['R_D_resource_v1.jsonl'].splitlines()]
assert resources[-1]['state']=='FAILED_STOP_NO_RETRY' and resources[-1]['exit_code']==1
assert all(x.get('output_bytes',0)==0 for x in resources)
copies=out/'frozen_remote_files';copies.mkdir()
for name,raw in files.items():(copies/name).write_bytes(raw)
receipt=dict(status='FORMAL_READ_ONLY_FAILED_AUTHORIZATION_FREEZE_PASS',request_sha256=rid,stable_before_after=True,exact_files=len(files),frozen_hashes={k:h(v) for k,v in files.items()},output_absent=True,worker_not_live=True,session_absent=True,failed_before_model_loading=True,training_updates=0,root_cause='Complete request SHA256 omitted from user_authorization_text',remote_mutations=False,retry_performed=False,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
(out/'failure_freeze_audit_v2.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
