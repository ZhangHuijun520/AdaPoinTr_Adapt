from pathlib import Path
import socket, os, subprocess, hashlib, json, time
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
assert hashlib.sha256((I / 'SCQ_RF_Sref_C_training_execution_request_v1.json').read_bytes()).hexdigest() == '6d63c000de45f02cee7e7318abedaef0bb96b39e32a5e0ae6f40bdfbf2c67b21'
q = json.loads((I / 'SCQ_RF_Sref_C_training_execution_request_v1.json').read_bytes())
import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in root.rglob('*'):
  if not p.is_file():continue
  assert not p.is_symlink() and p.stat().st_size<=2097152
  b=p.read_bytes();total+=len(b);assert len(files)<32 and total<=8388608
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
for i,r in enumerate([q['implementation'][k] for k in ('runtime','budget_parent','preflight_helper','native_helper','cuda_entry')]):
 p=Path(r['path']);b=p.read_bytes();total+=len(b);assert total<=8388608 and hashlib.sha256(b).hexdigest()==r['sha256']
 files['related/'+str(i)+'_'+p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_FAILURE_METADATA_READ',files=files,bytes=total)))
