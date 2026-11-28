
from pathlib import Path,PurePosixPath
import hashlib,json,base64,zlib,subprocess,shlex
d=Path(__file__).resolve().parent
rid="91522ab958d4294327256ef4113be9ff9206995c44d264611ce27bda5afa07fc"
root=d.parent
qpath=root/"EJTC_D1_R_D_training_execution_request_h7vvrr_v3.json"
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,data):
 with p.open("x",encoding="utf-8") as f:json.dump(data,f,indent=2,ensure_ascii=False)
assert sha(qpath.read_bytes())==rid
q=load(qpath)
m=load(d/"EJTC_R_D_h7vvrr_request_install_mapping_v3.json")
assert m["request_sha256"]==rid and len(m["files"])==1 and m["overwrite"] is False
a=load(root/"R_D_user_execution_authorization_v3.json")
assert a["request_sha256"]==rid and a["explicit_user_authorization"] is True
host=q["binding"]["identity"]["hostname"]
python=q["binding"]["identity"]["python_realpath"]
install=m["existing_install_root"]
output=q["binding"]["output"]
u=m["upload"]
w=["wsl.exe","-d","Ubuntu-20.04","--exec","/home/zhj/.local/bin/hpc5000"]
common=f"""import socket,os,json,hashlib,stat
from pathlib import Path
assert socket.gethostname()=={host!r} and os.getuid()==1000
def h(b):return hashlib.sha256(b).hexdigest()
"""
def cmd(code):
 compile(code,"<R-D-transport>","exec")
 b=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 c=python+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+b+'\')))"'
 assert len(c)<=2048,len(c)
 return c
def run(code,name):
 c=cmd(common+code)
 p=subprocess.run(w+["exec","--timeout","60","--",c],capture_output=True,timeout=75)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode("utf-8","replace")[-6000:],stderr=p.stderr.decode("utf-8","replace")[-6000:])
 save(d/(name+".json"),rec)
 if p.returncode:raise RuntimeError(name+" failed "+rec["stdout"])
 return json.loads(p.stdout)
assert json.loads((root/"post_installation_freeze_audit_v3/formal_post_installation_freeze_audit_v3.json").read_bytes())["status"]=="FORMAL_READ_ONLY_V3_POST_INSTALLATION_FREEZE_AUDIT_PASS"
scan=f"""import tarfile,io,subprocess
r=Path({install!r});o=Path({output!r});p=Path({u['path']!r})
for t in (r,o):
 assert t.parent.resolve(strict=True)==t.parent and t.parent.is_dir() and os.access(t.parent,os.W_OK|os.X_OK)
 assert (t==r and t.resolve(strict=True)==t and t.is_dir()) or (t==o and not os.path.lexists(t))
assert p.resolve()==p and stat.S_ISREG(p.lstat().st_mode)
b=p.read_bytes();assert len(b)=={u['bytes']} and h(b)=={u['sha256']!r}
s=Path(str(p)+'.sha256')
assert s.resolve()==s and s.is_file() and s.stat().st_size<=256 and s.read_text().split()==[h(b),p.name]
assert sorted(x.name for x in r.iterdir())==['EJTC_D1_R_D_training_execution_request_h7vvrr_v2.json', 'EJTC_D1_R_D_training_execution_request_h7vvrr_v3.json', 'EJTC_D1_common_contract_v1.json', 'R_D_authorization_v1.json', 'R_D_dispatch_v1.log', 'R_D_exit_code.txt', 'R_D_resource_v1.jsonl', 'R_D_runtime_v1.json', 'R_D_single_attempt_v1.log', 'ejtc_train_r_d_v2.py', 'launch_rbss_r_d_v1.py']
members=[]
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as a:
 for t in a:
  assert t.isfile() and '/' not in t.name and len(members)<1
  raw=a.extractfile(t).read();installed=(r/t.name);assert installed.resolve()==installed and installed.read_bytes()==raw
  members.append([t.name,t.size,h(raw)])
assert len(set(x[0] for x in members))==1
args=['/usr/bin/nvidia-smi','--id={q['binding']['identity']['gpu_uuid']}']
v=[x.strip() for x in subprocess.check_output(args+['--query-gpu=uuid,driver_version,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=8).split(',')]
assert v[:2]==[{q['binding']['identity']['gpu_uuid']!r},{q['binding']['identity']['driver_version']!r}]
assert int(v[2])<=256 and int(v[3])>=20480
assert not subprocess.check_output(args+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
s=os.statvfs(r.parent);free=s.f_bavail*s.f_frsize;assert free>={q['launch']['matrix_disk_budget_bytes']}
print(json.dumps(dict(members=members,gpu=v,disk_free=free,installed_request_verified=True,output_absent=True)))
"""
v=run(scan,"execution_precheck_v3")
expected=sorted([[r["member"],r["bytes"],r["sha256"]] for r in m["files"]])
assert sorted(v["members"])==expected
project=Path.cwd()
oldread=load(project/"outputs/bcsp_ejtc_20261127_v2/p1_cuda_preparation_v1/server_readonly_h7vvrr_v1/server_readiness_receipt_v1.json")
assets={p:rec["expected"] for p,rec in oldread["files"].items() if "training_input" not in rec["groups"]}
for rec in q["files"].values():
 if not PurePosixPath(rec["path"]).is_relative_to(PurePosixPath(install)):
  assets[rec["path"]]=[rec["bytes"],rec["sha256"]]
geo=project/"outputs/cranial_bcsp_geov1_20261024"
fold=load(geo/"consolidated_binding_v1/fold_binding.json")["folds"]["D"]
ids=fold["train_case_ids"]
with (geo/"real_data_qc_v1/manifest_8192.jsonl").open(encoding="utf-8") as f:
 rows={r["case_id"]:r for r in map(json.loads,f)}
parent=load(project/"outputs/bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json")
for cid in ids:
 rec=rows[cid];assets[str(PurePosixPath(parent["data_root"])/rec["point_path"])]=[Path(geo/"real_data_qc_v1"/rec["point_path"]).stat().st_size,rec["sha256"]]
assets[parent["order"]["path"]]=[parent["order"]["bytes"],parent["order"]["sha256"]]
for rec in m["reused_assets"].values():
 assets[rec["path"]]=[rec["bytes"],rec["sha256"]]
paths=list(assets)
read="""def read(name):
 p=Path(name);a=p.lstat();assert p.resolve()==p and stat.S_ISREG(a.st_mode)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
"""
for j in range(0,len(paths),10):
 batch=paths[j:j+10]
 observed=run(read+"print(json.dumps([read(p) for p in "+repr(batch)+"]))",f"v3_execution_asset_check_{j//10+1:02}")
 assert observed==[[p,*assets[p]] for p in batch], "reuse mismatch"
print("Verified",len(assets),"assets including all 315 training points",flush=True)
preserved=m["preserve_existing_files"]
for j in range(0,len(preserved),5):
 batch=preserved[j:j+5]
 observed=run(read+"print(json.dumps([read(p) for p in "+repr([x["path"] for x in batch])+"]))",f"v3_failure_preservation_{j}")
 assert [[x[0],x[2]] for x in observed]==[[x["path"],x["sha256"]] for x in batch]
v=run(scan,"immediate_prelaunch_reverification_v3")
assert sorted(v["members"])==expected

save(d/"execution_readiness_receipt_v3.json",dict(status="EXECUTION_READINESS_PASS",request_sha256=rid,assets=len(assets),training_inputs=315,training_started=False))
