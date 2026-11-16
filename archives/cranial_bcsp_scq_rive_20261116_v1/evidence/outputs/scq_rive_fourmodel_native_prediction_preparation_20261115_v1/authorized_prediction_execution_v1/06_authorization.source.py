import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.parent.is_dir() and not os.path.lexists(p.parent)
p.parent.mkdir(mode=0o700)
b=b'{\n  "schema": "bcsp-development-authorization-v1",\n  "request_sha256": "ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774",\n  "explicit_user_authorization": true,\n  "user_authorization_text": "\\u4e0b\\u4e00\\u6b65\\u5355\\u72ec\\u6388\\u6743\\u9884\\u6d4brequest\\u5b8c\\u6574SHA256\\u3002\\u552f\\u4e00\\u6240\\u6307\\u4e3a\\u4e0a\\u4e00\\u6761\\u5217\\u660e\\u7684 ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774\\uff1b\\u51bb\\u7ed3\\u8303\\u56f4\\u5185\\u552f\\u4e00\\u4e00\\u6b21\\u56db\\u6a21\\u578b420\\u6b21Native\\u9884\\u6d4b\\uff0c\\u5931\\u8d25\\u5373\\u505c\\uff0c\\u4e0d\\u81ea\\u52a8\\u91cd\\u8bd5\\uff0c\\u4e0d\\u8bad\\u7ec3\\u3001BNCal\\u6216\\u8bc4\\u5206\\uff0c\\u4e0d\\u589e\\u52a0forward\\u3002"\n}\n'
h='4eb6e3a82e1f45ba12a6f76bf11e938efe4aab5389858771ec680e16580091a6'
assert hashlib.sha256(b).hexdigest()==h
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status='CONTROL_EXACT_WRITTEN',path=str(p),bytes=len(b),sha256=h)))
