"""Read-only three final weight downloads, hash verification, no deserialization."""
from pathlib import Path
import base64,hashlib,json,subprocess,zlib
R=Path(__file__).resolve().parents[1];base=R/'outputs/bcsp_ejtc_20261127_v2';d=Path('E:/ResearchBackups/AdaPoinTr/BCSP_EJTC/2026-11-28_key_checkpoints_v3');d.mkdir(exist_ok=False)
q=json.loads((base/'native_rtj315_preparation_v1/EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes());i=dict(q['binding']['identity']);i['hostname']='shu-common-25721452-notebook-mt93wz-0'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
rows=[]
for arm,rec in q['checkpoints'].items():
 code=f'''import os,socket,json,hashlib,stat
from pathlib import Path
assert socket.gethostname()=={i['hostname']!r} and os.getuid()=={i['uid']}
p=Path({rec['path']!r});a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size=={rec['bytes']}
h=hashlib.sha256()
with p.open('rb') as f:
 for b in iter(lambda:f.read(4194304),b''):h.update(b)
z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
assert h.hexdigest()=={rec['sha256']!r}
print(json.dumps(dict(hostname=socket.gethostname(),bytes=a.st_size,sha256=h.hexdigest())))
'''
 compile(code,'<readonly-weight-hash>','exec');blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"';assert len(cmd)<=2048
 args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000']
 r=subprocess.run(args+['exec','--timeout','50','--',cmd],capture_output=True,timeout=60);put(d/(arm+'_remote_hash_call.json'),dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8','replace'),stderr=r.stderr.decode('utf-8','replace')));assert r.returncode==0
 target=d/f'EJTC_{arm}_D_seed2026112801_epoch99_step3900.pth';linux='/mnt/e/'+target.relative_to('E:/').as_posix()
 r=subprocess.run(args+['get',rec['path'],linux,'--timeout','240'],capture_output=True,timeout=260);put(d/(arm+'_download_call.json'),dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8','replace'),stderr=r.stderr.decode('utf-8','replace')));assert r.returncode==0
 assert target.stat().st_size==rec['bytes'] and sha(target)==rec['sha256']
 with Path(str(target)+'.sha256').open('x',encoding='ascii') as f:f.write(rec['sha256']+'  '+target.name+'\n')
 rows.append(dict(arm=arm,path=str(target),bytes=target.stat().st_size,sha256=sha(target),remote_source=rec['path']))
 print('Backed up and verified '+arm,flush=True)
receipt=dict(status='THREE_EJTC_FINAL_CHECKPOINTS_LOCAL_BACKUP_VERIFIED',files=rows,total_bytes=sum(r['bytes'] for r in rows),checkpoint_deserialization=False,server_writes=0,server_deletions=0,GitHub_checkpoint_upload=False)
put(d/'checkpoint_backup_receipt_v1.json',receipt);put(base/'EJTC_checkpoint_backup_receipt_v1.json',receipt);print(json.dumps(receipt))
