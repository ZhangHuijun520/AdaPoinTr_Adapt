from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_RF_ten_memory_execution_request_v1.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == '51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'
q = json.loads(qp.read_bytes())
import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in sorted(root.rglob('*')):
  if not p.is_file() or (root==O and p.suffix in ('.gz','.npz')):continue
  assert not p.is_symlink() and p.stat().st_size<8388608
  b=p.read_bytes();total+=len(b);assert total<16777216
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READ',files=files,bytes=total)))
