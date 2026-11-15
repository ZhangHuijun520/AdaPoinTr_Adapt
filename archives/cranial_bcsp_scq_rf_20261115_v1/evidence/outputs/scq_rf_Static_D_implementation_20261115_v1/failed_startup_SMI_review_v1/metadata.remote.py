from pathlib import Path
import socket, os, hashlib, json, subprocess, base64
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v1')
assert not any((p.is_symlink() for p in (root, *root.parents, out, *out.parents)))
assert hashlib.sha256((root / 'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes()).hexdigest() == 'b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'
q = json.loads((root / 'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes())
files={};total=0
paths=[(label+'/'+str(f.relative_to(p)),f) for label,p in [('output',out),('installed',root)] for f in sorted(p.rglob('*')) if f.is_file()]
paths.append(('helper/preflight_helper.py',Path(q['implementation']['preflight_helper']['path'])))
assert len(paths)<=24
for name,p in paths:
 assert not p.is_symlink() and p.stat().st_size<=2097152
 raw=p.read_bytes();total+=len(raw);assert total<=8388608
 files[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),base64=base64.b64encode(raw).decode())
print(json.dumps(dict(status='BOUNDED_METADATA_READBACK',files=files,total_bytes=total)))
