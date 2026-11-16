import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1/authorization_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.parent.parent.is_dir() and not os.path.lexists(p.parent.parent)
p.parent.parent.mkdir(mode=0o700)
p.parent.mkdir(mode=0o700)
b=b'{\n  "schema": "bcsp-rive-training-authorization-v1",\n  "request_sha256": "fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda",\n  "explicit_user_authorization": true,\n  "user_authorization_text": "\\u660e\\u786e\\u6388\\u6743SHA256\\u4e3a fdcb6cacef71bfae9395baf7b3bd05506b34b4053b75bfb03f54bff6bbe82bda \\u7684request\\uff1b\\u91cd\\u9a8c\\u8d44\\u6e90\\u3001\\u8f93\\u5165\\u548c\\u8f93\\u51fa\\u8def\\u5f84\\u540e\\uff0c\\u542f\\u52a8\\u552f\\u4e00\\u4e00\\u6b21Static_C\\u30018k\\u21928k\\u30013900\\u6b65\\u8bad\\u7ec3\\u3002\\u5931\\u8d25\\u5373\\u505c\\uff0c\\u4e0d\\u81ea\\u52a8\\u91cd\\u8bd5\\u6216resume\\uff0c\\u4e0d\\u8fd0\\u884c\\u8bc4\\u4ef7\\u6216BNCal\\u3002"\n}\n'
h='e00e2273fbdf052160071a7a1b4c69403c7970821c0624c9ab92c52808f8575d'
assert hashlib.sha256(b).hexdigest()==h
with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status="CONTROL_EXACT_WRITTEN",path=str(p),bytes=len(b),sha256=h)))
