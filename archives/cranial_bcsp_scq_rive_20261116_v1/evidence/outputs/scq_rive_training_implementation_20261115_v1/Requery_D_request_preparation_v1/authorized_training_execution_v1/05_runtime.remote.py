import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/runtime_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.is_dir()
assert hashlib.sha256((p.parent/'authorization_v1.json').read_bytes()).hexdigest()=='a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e'
b=b'{\n  "schema": "bcsp-rive-training-runtime-v1",\n  "request_sha256": "c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1",\n  "authorization_sha256": "a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e"\n}\n'
h='4fb7ad4408456198daabb01b81e6e8ff8cf877f67cb8f01437364b1a6b76bcb0'
assert hashlib.sha256(b).hexdigest()==h
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status='CONTROL_EXACT_WRITTEN',path=str(p),bytes=len(b),sha256=h)))
