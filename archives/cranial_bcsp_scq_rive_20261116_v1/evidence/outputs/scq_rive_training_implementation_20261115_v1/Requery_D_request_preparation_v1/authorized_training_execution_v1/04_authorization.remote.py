import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/authorization_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.parent.is_dir() and not os.path.lexists(p.parent)
p.parent.mkdir(mode=0o700)
b=b'{\n  "schema": "bcsp-rive-training-authorization-v1",\n  "request_sha256": "c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1",\n  "explicit_user_authorization": true,\n  "user_authorization_text": "\\u4e0b\\u4e00\\u6b65\\u5355\\u72ec\\u6388\\u6743 Requery_D\\u8bad\\u7ec3request \\u5b8c\\u6574SHA256\\u3002\\u552f\\u4e00\\u6240\\u6307\\u4e3a\\u4e0a\\u4e00\\u6761\\u5217\\u660e\\u7684 c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1\\uff1b\\u51bb\\u7ed3\\u8303\\u56f4\\u5185\\u552f\\u4e00\\u4e00\\u6b21\\u8bad\\u7ec3\\uff0c\\u5931\\u8d25\\u5373\\u505c\\uff0c\\u4e0d\\u81ea\\u52a8\\u91cd\\u8bd5\\u6216resume\\uff0c\\u4e0d\\u8fd0\\u884c\\u8bc4\\u4ef7\\u6216BNCal\\u3002"\n}\n'
h='a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e'
assert hashlib.sha256(b).hexdigest()==h
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status='CONTROL_EXACT_WRITTEN',path=str(p),bytes=len(b),sha256=h)))
