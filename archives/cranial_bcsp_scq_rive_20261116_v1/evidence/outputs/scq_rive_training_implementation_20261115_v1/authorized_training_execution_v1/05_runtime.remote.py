import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1/runtime_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.is_dir()
assert hashlib.sha256((p.parent/"authorization_v1.json").read_bytes()).hexdigest()=='e00e2273fbdf052160071a7a1b4c69403c7970821c0624c9ab92c52808f8575d'
b=b'{\n  "schema": "bcsp-rive-training-runtime-v1",\n  "request_sha256": "fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda",\n  "authorization_sha256": "e00e2273fbdf052160071a7a1b4c69403c7970821c0624c9ab92c52808f8575d"\n}\n'
h='d48506eb32d1476746de04e85d151df04f36c81dea8138ad2fafbbf085e26e6a'
assert hashlib.sha256(b).hexdigest()==h
with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status="CONTROL_EXACT_WRITTEN",path=str(p),bytes=len(b),sha256=h)))
