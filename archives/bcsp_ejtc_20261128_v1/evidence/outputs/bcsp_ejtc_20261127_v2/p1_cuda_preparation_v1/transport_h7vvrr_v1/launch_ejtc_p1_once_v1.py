
from pathlib import Path,PurePosixPath
import base64,hashlib,json,shlex,subprocess,sys,zlib
d=Path(__file__).resolve().parent
rid="1cb96ed253b91cf9248b768934da3f8e48276ca160aa74d9efa8fcb76e4b8a80"
mid="43ccb0e4656ad30727f1b5ac624fee600783dda69988505db7c5dc92e372c8d9"
def sha(b):return hashlib.sha256(b).hexdigest()
def pack(x):return json.dumps(x,separators=(",",":"),ensure_ascii=True).encode()
def read(name):return (d/name).read_bytes()
def put(name,obj):
 with (d/name).open("xb") as f:f.write(pack(obj)+b"\n")
m=read("EJTC_P1_CUDA_h7vvrr_install_mapping_v1.json")
assert sha(m)==mid
m=json.loads(m)
ins=json.loads(read("installation_receipt_v1.json"))
assert ins["status"]=="EJTC_P1_NO_OVERWRITE_INSTALL_PASS" and ins["mapping_sha256"]==mid and ins["request_sha256"]==rid
root=PurePosixPath(m["new_install_root"])
files={v["member"]:v for v in m["files"]}
n=[k for k in files if k.endswith("_request_h7vvrr_v1.json")]
assert len(n)==1 and files[n[0]]["sha256"]==rid
qraw=(d.parent/"server_readonly_h7vvrr_v1"/n[0]).read_bytes()
assert sha(qraw)==rid
q=json.loads(qraw)
assert q["counts"]==dict(forward=53,base_loss=51,auxiliary=46,autograd_grad=32,backward=39,optimizer_steps=0)
fingerprint=sha(pack(sorted([r["member"],r["bytes"],r["sha256"]] for r in m["files"])))
assert fingerprint==ins["members_sha256"]
auth=pack(dict(schema="bcsp-development-authorization-v1",request_sha256=rid,explicit_user_authorization=True,
    user_authorization_text="User explicitly authorized one CUDA zero-update admission for "+rid))
rt=pack(dict(schema="bcsp-development-runtime-v1",request_sha256=rid,authorization_sha256=sha(auth)))
host=q["identity"]["hostname"]
python=q["identity"]["python_realpath"]
gpu=q["identity"]["gpu_uuid"]
req,ap,rp=q["control_paths"]
out=q["output"]
session="bcsp_ejtc_p1_h7vvrr_v1"
cli=["wsl.exe","-d","Ubuntu-20.04","--exec","/home/zhj/.local/bin/hpc5000","exec","--timeout","45","--"]
code=f"""import hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert socket.gethostname()=={host!r} and os.getuid()==1000
def h(b):return hashlib.sha256(b).hexdigest()
r=Path({str(root)!r});o=Path({out!r})
assert r.resolve(strict=True)==r and o.parent.resolve(strict=True)==o.parent
rows=[]
for p in r.rglob('*'):
 assert p.resolve()==p
 if p.is_file():
  b=p.read_bytes();rows.append([p.relative_to(r).as_posix(),len(b),h(b)])
 else:assert p==r/'labels'
assert len(rows)==43 and h(json.dumps(sorted(rows),separators=(',',':')).encode())=={fingerprint!r}
assert not os.path.lexists(o)
def check(f):
 return subprocess.check_output(['/usr/bin/nvidia-smi','--id='+{gpu!r},f,'--format=csv,noheader,nounits'],text=True,timeout=8).strip()
values=[x.strip() for x in check('--query-gpu=uuid,driver_version,memory.used,memory.free').split(',')]
assert values[:2]==[{gpu!r},{q['identity']['driver_version']!r}] and int(values[2])<=256 and int(values[3])>=20480
assert not check('--query-compute-apps=pid')
v=os.statvfs(o.parent);assert v.f_bavail*v.f_frsize>=4294967296
s={session!r}
assert subprocess.run(['tmux','has-session','-t','='+s],capture_output=True).returncode==1
"""
cmd=[python,"-I","-S","-B",q["bindings"]["worker"]["path"],"--request",req,"--request-sha256",rid,
     "--authorization",ap,"--authorization-sha256",sha(auth),"--runtime",rp,"--runtime-sha256",sha(rt)]
worker="env CUDA_VISIBLE_DEVICES="+gpu+" "+shlex.join(cmd)
log=str(root/"single_attempt.log")
exit_path=str(root/"exit_code.txt")
shell_worker=f"{worker} > {shlex.quote(log)} 2>&1; rc=$?; (set -C; printf '%s\\n' \"$rc\" > {shlex.quote(exit_path)})"
# Keep the verification and the single materialization in distinct bounded calls.
def transport(code):
 compile(code,"<ejtc-launch>","exec")
 b=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 command=python+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+b+'\')))"'
 assert len(command)<=2048,len(command)
 return command
check_command=transport(code+"print(json.dumps(dict(host=socket.gethostname(),files=len(rows),gpu=values,free=v.f_bavail*v.f_frsize)))")
launch=f"""import os,socket,hashlib,subprocess,json
from pathlib import Path
assert socket.gethostname()=={host!r} and os.getuid()==1000
r=Path({str(root)!r}); assert r.resolve(strict=True)==r
assert not any(os.path.lexists(p) for p in [{out!r},{ap!r},{rp!r},{log!r},{exit_path!r}])
assert hashlib.sha256(Path({req!r}).read_bytes()).hexdigest()=={rid!r}
s={session!r}
assert subprocess.run(['tmux','has-session','-t','='+s],capture_output=True).returncode==1
for p,v in (({ap!r},{auth!r}),({rp!r},{rt!r})):
 with open(p,'xb') as f:f.write(v)
subprocess.run(['tmux','new-session','-d','-s',s,{shell_worker!r}],check=True,timeout=10)
print(json.dumps(dict(host=socket.gethostname(),session=s,started=True)))
"""
launch_command=transport(launch)
def remote(command,label):
 p=subprocess.run(cli+[command],capture_output=True,timeout=60)
 result=dict(returncode=p.returncode,stdout=p.stdout.decode("utf-8","replace")[-4000:])
 put(label,result)
 print(json.dumps(result),flush=True)
 return p
assert not (d/"cuda_launch_attempt_v1.json").exists() and not (d/"cuda_prelaunch_readback_v1.json").exists()
p=remote(check_command,"cuda_prelaunch_readback_v1.json")
assert p.returncode==0 and json.loads(p.stdout)["files"]==43
put("cuda_launch_claim_v1.json",dict(request_sha256=rid,authorization_sha256=sha(auth),runtime_sha256=sha(rt),attempts=1))
p=remote(launch_command,"cuda_launch_attempt_v1.json")
assert p.returncode==0 and json.loads(p.stdout)["started"]

