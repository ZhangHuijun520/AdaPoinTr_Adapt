import pathlib,json,hashlib,os,socket,shutil,subprocess,shlex
P=pathlib.Path
root=P("/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1");run="SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1"
p=root/(run+"_execution_request_v1.json");b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=="45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de"
q=json.loads(b);I=q["identity"];L=q["launch_contract"]
assert socket.gethostname()==I["hostname"] and os.getuid()==1000
for path in (q["output"],q["launch_attempt"]):
 p=P(path);assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
for name,h in [("authorization_path","629cf796979a5d20cd49d02dd4523c498de95097ea70d66b8c1bc55234c16842"),("runtime_path","6c736b2af39c12e1a83fa37a0512c18ef1b43235394fce3228ed2fb0a721379c"),("launcher_path","a9f5e7c7b2a74d225c4ca443e5b60d4bcd0e471e1487b9043bfb622a599a865f")]:
 p=P(L[name]);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and hashlib.sha256(p.read_bytes()).hexdigest()==h
session=L["tmux_session"];assert subprocess.run(["tmux","has-session","-t","="+session],capture_output=True).returncode==1
args=["/usr/bin/nvidia-smi","--id="+I["gpu_uuid"],"--query-gpu=uuid,name,driver_version,memory.total,memory.used","--format=csv,noheader,nounits"]
gpu=[s.strip() for s in subprocess.check_output(args,text=True,timeout=10).strip().split(",")];assert gpu[:4]==[I["gpu_uuid"],I["gpu_name"],I["driver_version"],str(I["nvidia_smi_memory_total_MiB"])] and int(gpu[4])<=256
assert shutil.disk_usage(I["project"]).free>=6442450944
with P(q["launch_attempt"]).open("x") as f:json.dump(dict(status="CLAIMED_BEFORE_TMUX",request_sha256="45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de"),f);f.flush();os.fsync(f.fileno())
r=subprocess.run(["tmux","new-session","-d","-s",session,"bash "+shlex.quote(L["launcher_path"])],capture_output=True,text=True,timeout=10)
print(json.dumps(dict(status="SINGLE_TMUX_SUBMIT_RESULT",returncode=r.returncode,session=session,stdout=r.stdout,stderr=r.stderr,gpu=gpu)),flush=True)
assert r.returncode==0
