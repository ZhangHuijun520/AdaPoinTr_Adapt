from pathlib import Path
import base64, hashlib, json, subprocess, zlib

d = Path(__file__).resolve().parent
m = json.loads((d / 'EJTC_R_D_h7vvrr_install_mapping_v2.json').read_bytes())
assert hashlib.sha256((d / 'EJTC_R_D_h7vvrr_transport_v2.tar.gz').read_bytes()).hexdigest() == m['upload']['sha256']
expected = sorted([[r['member'], r['bytes'], r['sha256']] for r in m['files']])
code = f'''import os,socket,json,hashlib,tarfile,io,stat
from pathlib import Path
assert socket.gethostname()=={m['identity']['hostname']!r} and os.getuid()==1000
p=Path({m['upload']['path']!r})
assert p.resolve(strict=True)==p and stat.S_ISREG(p.lstat().st_mode)
b=p.read_bytes(); h=hashlib.sha256(b).hexdigest()
assert len(b)=={m['upload']['bytes']} and h=={m['upload']['sha256']!r}
s=Path(str(p)+'.sha256')
assert s.resolve(strict=True)==s and s.is_file() and s.stat().st_size<=256
assert s.read_text().split()==[h,p.name]
rows=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as a:
 for t in a:
  assert t.isfile() and '/' not in t.name and len(rows)<4
  rows.append([t.name,t.size,hashlib.sha256(a.extractfile(t).read()).hexdigest()])
assert sorted(rows)=={expected!r}
absent=[]
for name in { [m['new_install_root'],m['output_must_be_absent']]+m['runtime_controls_must_be_absent']!r}:
 assert not os.path.lexists(name)
 absent.append(name)
for name in {[m['new_install_root'],m['output_must_be_absent']]!r}:
 p=Path(name).parent
 assert p.resolve(strict=True)==p and p.is_dir()
print(json.dumps(dict(status='READ_ONLY_UPLOAD_VERIFICATION_PASS',hostname=socket.gethostname(),uid=os.getuid(),upload_bytes=len(b),upload_sha256=h,members=rows,absent=absent,installed=False,training_started=False)))
'''
compile(code, '<readonly-upload>', 'exec')
encoded = base64.b64encode(zlib.compress(code.encode(), 9)).decode()
command = m['identity']['python_realpath'] + ' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\'' + encoded + '\')))"'
assert len(command.encode()) <= 2048
p = subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','55','--',command],capture_output=True,timeout=65)
receipt = dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'),request_sha256=m['request_sha256'],remote_mutations=False)
with (d/'upload_readonly_verification_receipt_v2.json').open('x',encoding='utf-8') as f:
 json.dump(receipt,f,ensure_ascii=False,indent=2)
assert p.returncode == 0, receipt
r=json.loads(receipt['stdout'])
assert r['status']=='READ_ONLY_UPLOAD_VERIFICATION_PASS'
print(json.dumps(r,ensure_ascii=False))
