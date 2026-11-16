import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1/authorization_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.parent.is_dir() and not os.path.lexists(p.parent)
p.parent.mkdir(mode=0o700)
b=b'{\n  "schema": "bcsp-rive-training-authorization-v1",\n  "request_sha256": "45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de",\n  "explicit_user_authorization": true,\n  "user_authorization_text": "\\u7528\\u6237\\u672c\\u8f6e\\u539f\\u6587\\uff1a\\u4e0b\\u4e00\\u6b65\\u5355\\u72ec\\u660e\\u786e\\u6388\\u6743Requery_C\\u8bad\\u7ec3request\\u5b8c\\u6574SHA256\\u3002\\u552f\\u4e00\\u6240\\u6307\\u4e3a\\u4e0a\\u4e00\\u6761\\u5df2\\u5217\\u660e\\u7684 45d37fc024dd4e97a82cd08c93ad25cebfcbd4a4f74ae8b2be9d22e4536392de\\uff1b\\u8303\\u56f4\\u4e3a\\u51bb\\u7ed3request\\u7684\\u552f\\u4e00\\u4e00\\u6b21\\u8bad\\u7ec3\\uff0c\\u5931\\u8d25\\u5373\\u505c\\uff0c\\u4e0d\\u81ea\\u52a8\\u91cd\\u8bd5/resume\\uff0c\\u4e0d\\u8bc4\\u4ef7\\u6216BNCal\\u3002"\n}\n'
h='629cf796979a5d20cd49d02dd4523c498de95097ea70d66b8c1bc55234c16842'
assert hashlib.sha256(b).hexdigest()==h
with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status="CONTROL_EXACT_WRITTEN",path=str(p),bytes=len(b),sha256=h)))
