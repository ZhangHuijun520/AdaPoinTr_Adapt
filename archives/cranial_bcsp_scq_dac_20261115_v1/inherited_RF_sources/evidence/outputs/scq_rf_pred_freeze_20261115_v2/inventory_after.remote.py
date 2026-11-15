from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == '5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9'
q = json.loads(qp.read_bytes())
def inventory(root):
 files={};dirs=[];total=0
 for p in [root,*sorted(root.rglob('*'))]:
  assert not p.is_symlink() and (p.is_file() or p.is_dir()),str(p)
  n=str(p.relative_to(root))
  if p.is_dir():dirs.append(n);continue
  b=p.stat();total+=b.st_size;assert len(files)<800 and b.st_size<1073741824 and total<2147483648
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  a=p.stat();fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
  assert fp(b)==fp(a)
  files[n]=dict(bytes=a.st_size,sha256=h.hexdigest(),fingerprint=fp(a))
 return dict(files=files,directories=dirs,hashed_bytes=total)
print(json.dumps(dict(status='EXACT_INVENTORY_AND_STABLE_HASHES',output=inventory(O),installed=inventory(I))))
