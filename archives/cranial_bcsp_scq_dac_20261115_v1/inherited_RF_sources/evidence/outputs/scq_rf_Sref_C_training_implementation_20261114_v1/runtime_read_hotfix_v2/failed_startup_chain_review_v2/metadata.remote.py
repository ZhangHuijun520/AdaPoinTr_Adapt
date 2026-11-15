from pathlib import Path
import socket, os, subprocess, hashlib, json, time
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
assert hashlib.sha256((I / 'SCQ_RF_Sref_C_training_execution_request_v2.json').read_bytes()).hexdigest() == 'b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1'
q = json.loads((I / 'SCQ_RF_Sref_C_training_execution_request_v2.json').read_bytes())
import base64
files={};total=0
for root,label in [(O,'output'),(I,'installed')]:
 for p in root.rglob('*'):
  if not p.is_file():continue
  assert not p.is_symlink() and p.stat().st_size<=2097152
  b=p.read_bytes();total+=len(b);assert len(files)<40 and total<=8388608
  files[label+'/'+str(p.relative_to(root))]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
for i,r in enumerate([r for k,r in q['implementation'].items() if k!='entry']+[q['initialization']]):
 p=Path(r['path']);b=p.read_bytes();total+=len(b);assert total<=8388608 and hashlib.sha256(b).hexdigest()==r['sha256']
 files['related/'+str(i)+'_'+p.name]=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),base64=base64.b64encode(b).decode())
print(json.dumps(dict(status='BOUNDED_FAILURE_METADATA_READ',files=files,bytes=total)))
