import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1/runtime_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.is_dir()
assert hashlib.sha256((p.parent/"authorization_v1.json").read_bytes()).hexdigest()=='629cf796979a5d20cd49d02dd4523c498de95097ea70d66b8c1bc55234c16842'
b=b'{\n  "schema": "bcsp-rive-training-runtime-v1",\n  "request_sha256": "45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de",\n  "authorization_sha256": "629cf796979a5d20cd49d02dd4523c498de95097ea70d66b8c1bc55234c16842"\n}\n'
h='6c736b2af39c12e1a83fa37a0512c18ef1b43235394fce3228ed2fb0a721379c'
assert hashlib.sha256(b).hexdigest()==h
with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status="CONTROL_EXACT_WRITTEN",path=str(p),bytes=len(b),sha256=h)))
