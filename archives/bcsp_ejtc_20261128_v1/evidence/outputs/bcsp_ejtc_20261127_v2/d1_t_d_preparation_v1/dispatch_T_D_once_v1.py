
from pathlib import Path,PurePosixPath
import hashlib,json,base64,zlib,shlex,subprocess
d=Path("outputs/bcsp_ejtc_20261127_v2/d1_t_d_preparation_v1").resolve()
t=d/"transport_h7vvrr_v1"
qf=d/"EJTC_D1_T_D_training_execution_request_h7vvrr_v1.json"
h=lambda b:hashlib.sha256(b).hexdigest()
rid=h(qf.read_bytes())
assert rid=="0764f6a292b0d05f1bf5a6c964adac22d7b2c3ae1e8147cd08260c5b5b38cb22"
q=json.loads(qf.read_bytes())
assert json.loads((d/"execution_readiness_v1/T_D_execution_readiness_receipt_v1.json").read_bytes())["status"]=="T_D_EXECUTION_READINESS_PASS"
auth=json.loads((d/"T_D_user_execution_authorization_v1.json").read_bytes())
assert auth["request_sha256"]==rid and auth["explicit_user_authorization"] is True and rid in auth["user_authorization_text"]
auth_raw=json.dumps(auth,separators=(",",":"),ensure_ascii=True).encode()
runtime=json.dumps(dict(schema="bcsp-development-runtime-v1",request_sha256=rid,authorization_sha256=h(auth_raw)),separators=(",",":")).encode()
assert auth_raw==(d/"T_D_user_execution_authorization_v1.json").read_bytes()
assert runtime==(d/"T_D_local_runtime_material_v1.json").read_bytes()
import runpy
worker=Path("outputs/bcsp_ejtc_20261127_v2/d1_t_d_preparation_v1/ejtc_train_t_d_v1.py").resolve()
assert h(worker.read_bytes())==q['files']['worker']['sha256']
env=runpy.run_path(str(worker),run_name='dispatch_authorize_prewrite_check')
env['authorize'](q,rid,json.loads(auth_raw),h(auth_raw),json.loads(runtime))

i=q["binding"]["identity"];p=q["launch"]
cmd=[i["python_realpath"],"-I","-S","-B",p["launcher"]["path"]]
for key,val in [("request",p["request_path"]),("request-sha256",rid),("authorization",p["authorization_path"]),
                ("authorization-sha256",h(auth_raw)),("runtime",p["runtime_path"]),("runtime-sha256",h(runtime))]:
 cmd+=["--"+key,val]
log=p["dispatch_log"]
exitfile=p["exit_code_path"]
shell=shlex.join(cmd)+" > "+shlex.quote(log)+" 2>&1; rc=$?; (set -C; printf '%s\\n' \"$rc\" > "+shlex.quote(exitfile)+")"
session=p["session_name"]
code=f"""import os,socket,json,hashlib,subprocess
from pathlib import Path,PurePosixPath
assert socket.gethostname()=={i['hostname']!r} and os.getuid()==1000
assert hashlib.sha256(Path({p['request_path']!r}).read_bytes()).hexdigest()=={rid!r}
assert all(not os.path.lexists(p) for p in {[q['binding']['output'],p['authorization_path'],p['runtime_path'],p['single_attempt_log'],p['resource_log'],log,exitfile]!r})
assert subprocess.run(['tmux','has-session','-t','='+{session!r}],capture_output=True).returncode==1
for f,b in (({p['authorization_path']!r},{auth_raw!r}),({p['runtime_path']!r},{runtime!r})):
 assert Path(f).parent.resolve()==Path(f).parent
 with open(f,'xb') as out:out.write(b)
subprocess.run(['tmux','new-session','-d','-s',{session!r},{shell!r}],check=True,timeout=10)
print(json.dumps(dict(host=socket.gethostname(),session={session!r},started=True,request_sha256={rid!r})))
"""
blob=base64.b64encode(zlib.compress(code.encode(),9)).decode()
command=i["python_realpath"]+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
assert len(command)<=2048
receipt=t/"single_training_dispatch_T_D_v1.json"
assert not receipt.exists()
p=subprocess.run(["wsl.exe","-d","Ubuntu-20.04","--exec","/home/zhj/.local/bin/hpc5000","exec","--timeout","25","--",command],capture_output=True,timeout=40)
r=dict(returncode=p.returncode,stdout=p.stdout.decode("utf-8","replace")[-3000:],stderr=p.stderr.decode("utf-8","replace")[-3000:],request_sha256=rid)
with receipt.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2)
print(json.dumps(r),flush=True)
assert p.returncode==0 and json.loads(p.stdout)["started"]

