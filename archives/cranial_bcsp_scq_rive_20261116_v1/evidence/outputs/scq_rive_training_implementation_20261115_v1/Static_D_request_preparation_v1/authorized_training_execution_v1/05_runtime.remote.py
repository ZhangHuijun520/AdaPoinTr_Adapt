import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Static_foldD_seed0_train_20261115_v1/runtime_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.is_dir()
assert hashlib.sha256((p.parent/'authorization_v1.json').read_bytes()).hexdigest()=='88c86367a77a285832558dff06dd228a26ae5e7cffb036c8717197c3365c3b1b'
b=b'{\n  "schema": "bcsp-rive-training-runtime-v1",\n  "request_sha256": "f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2",\n  "authorization_sha256": "88c86367a77a285832558dff06dd228a26ae5e7cffb036c8717197c3365c3b1b"\n}\n'
h='d3af655fad89331b97482d0e6be3cce7f3a1e8b9275f0d4451d895d8f39cd4af'
assert hashlib.sha256(b).hexdigest()==h
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status='CONTROL_EXACT_WRITTEN',path=str(p),bytes=len(b),sha256=h)))
