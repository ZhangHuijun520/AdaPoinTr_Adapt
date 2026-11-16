import pathlib,os,socket,hashlib,json
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json')
assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents))
assert p.parent.is_dir()
assert hashlib.sha256(P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json').read_bytes()).hexdigest()=='4eb6e3a82e1f45ba12a6f76bf11e938efe4aab5389858771ec680e16580091a6'
b=b'{\n  "schema": "bcsp-development-runtime-v1",\n  "request_sha256": "ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774",\n  "authorization_sha256": "4eb6e3a82e1f45ba12a6f76bf11e938efe4aab5389858771ec680e16580091a6"\n}\n'
h='b51af90679fcbe8c16fd25d452eb0d2b8f42601ebffe9ecb1aa068239fc7bc31'
assert hashlib.sha256(b).hexdigest()==h
with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==len(b) and hashlib.sha256(p.read_bytes()).hexdigest()==h
print(json.dumps(dict(status='CONTROL_EXACT_WRITTEN',path=str(p),bytes=len(b),sha256=h)))
