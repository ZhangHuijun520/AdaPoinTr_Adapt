
"""One-shot exact no-overwrite installation for the authorized EJTC bundle."""
from pathlib import Path, PurePosixPath
import base64,json,hashlib,subprocess,zlib

d=Path(__file__).resolve().parent
m=d/"EJTC_P1_CUDA_h7vvrr_install_mapping_v1.json"
mapping_sha="43ccb0e4656ad30727f1b5ac624fee600783dda69988505db7c5dc92e372c8d9"
def sha(x): 
 return hashlib.sha256(x).hexdigest()
raw=m.read_bytes()
assert sha(raw)==mapping_sha
q=json.loads(raw)
upload=d/"upload_readonly_receipt_v1.json"
assert sha(upload.read_bytes())=="02646ad803761042dbcdfff4a1cf0ac51c23a2d120a90ad7b8e79668107906ed"
assert json.loads(upload.read_bytes())["status"]=="EJTC_P1_UPLOAD_READ_ONLY_PASS"
root=PurePosixPath(q["new_install_root"])
files=q["files"];existing=q["reused_assets"];u=q["upload"]
assert q["overwrite"] is False and q["execution_authorized"] is False
assert len(files)==len({r["target"] for r in files})==43 and len(existing)==99
assert q["directories_to_create"]==[str(root),str(root/"labels")]
assert all(root/r["member"]==PurePosixPath(r["target"]) for r in files)
host=q["identity"]["hostname"]
command=["wsl.exe","-d","Ubuntu-20.04","--exec","/home/zhj/.local/bin/hpc5000","exec","--timeout","55","--"]
common=f"""import socket,os,json,hashlib,stat
from pathlib import Path
assert socket.gethostname()=={host!r} and os.getuid()==1000
def h(b):return hashlib.sha256(b).hexdigest()
"""
def compile_remote(code):
 compile(code,"<remote-install>","exec")
 blob=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 shell='/opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(shell.encode())<=2048,len(shell.encode())
 return shell

def run(shell):
 p=subprocess.run(command+[shell],capture_output=True,timeout=75)
 if p.returncode:
  print(p.stdout.decode("utf-8","replace")[-1200:],flush=True)
  raise ValueError(f"remote command returned {p.returncode}")
 return json.loads(p.stdout)
def canonical(rows):
 return json.dumps(sorted(rows),separators=(",",":")).encode()
fingerprint=sha(canonical([[r["member"],r["bytes"],r["sha256"]] for r in files]))
install=f"""import io,tarfile
r=Path({str(root)!r});o=Path({q['output_must_be_absent']!r})
p=Path({u['path']!r});s=Path(str(p)+'.sha256')
for t in (r,o):
 assert t.parent.resolve(strict=True)==t.parent and t.parent.is_dir() and not os.path.lexists(t) and os.access(t.parent,os.W_OK|os.X_OK)
assert p.resolve()==p and stat.S_ISREG(p.lstat().st_mode) and p.stat().st_size=={u['bytes']}
assert s.resolve()==s and stat.S_ISREG(s.lstat().st_mode) and s.stat().st_size<=256
raw=p.read_bytes();assert len(raw)=={u['bytes']} and h(raw)=={u['sha256']!r}
assert s.read_text(encoding='ascii').split()==[h(raw),p.name]
data={{}}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:
 for t in a:
  n=Path(t.name)
  assert t.isfile() and t.name not in data and not n.is_absolute() and '..' not in n.parts
  assert len(n.parts)==1 or (len(n.parts)==2 and n.parts[0]=='labels')
  assert len(data)<43
  data[t.name]=a.extractfile(t).read()
def sig(data):return h(json.dumps(sorted([k,len(v),h(v)] for k,v in data.items()),separators=(',',':')).encode())
assert len(data)==43 and sig(data)=={fingerprint!r}
assert not os.path.lexists(o)
r.mkdir();(r/'labels').mkdir()
for k,v in data.items():
 with (r/k).open('xb') as f:f.write(v)
z={{v.relative_to(r).as_posix():v.read_bytes() for v in r.rglob('*') if v.is_file()}}
assert len(z)==43 and sig(z)==sig(data) and not os.path.lexists(o)
assert all(not os.path.lexists(r/x) for x in ('authorization_v1.json','runtime_v1.json'))
print(json.dumps(dict(host=socket.gethostname(),installed=len(z),members_sha256=sig(z),root=str(r),output_absent=True,runtime_controls_absent=True)))
"""
install_command=compile_remote(common+install)
recheck="""def record(s):
 p=Path(s);a=p.lstat()
 assert p.resolve()==p and stat.S_ISREG(a.st_mode)
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):d.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 return [s,a.st_size,d.hexdigest()]
"""
batches=[existing[i:i+10] for i in range(0,len(existing),10)]
probes=[(batch,compile_remote(common+recheck+"print(json.dumps([record(p) for p in "+repr([r["path"] for r in batch])+"]))"))
        for batch in batches]
receipt=d/"installation_receipt_v1.json"
assert not receipt.exists()
for batch,cmd in probes:
 observed=run(cmd)
 assert observed==[[r["path"],r["bytes"],r["sha256"]] for r in batch], "reused asset mismatch"
print("Verified 99 reused files and container identity",flush=True)
actual=run(install_command)
assert actual["host"]==host and actual["installed"]==43 and actual["members_sha256"]==fingerprint
assert actual["output_absent"] and actual["runtime_controls_absent"]
with receipt.open("x",encoding="utf-8") as f:
 json.dump(dict(status="EJTC_P1_NO_OVERWRITE_INSTALL_PASS",mapping_sha256=mapping_sha,request_sha256=q["request_sha256"],
                reuse_verified=99,execution_started=False,**actual),f,indent=2)
print(json.dumps(actual),flush=True)

