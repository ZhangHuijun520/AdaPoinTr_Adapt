from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_BS_CD_native_prediction_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'
q = json.loads(qp.read_bytes())
import tarfile
c=json.loads((O/'completion.json').read_bytes());rs={r['name']:r for r in c['archive']['members']}
assert len(rs)==len(c['archive']['members'])==426
with tarfile.open(O/'development_predictions_v1.tar.gz') as t:
 ms=t.getmembers();assert len(ms)==426 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<8388608
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
print(json.dumps(dict(status='ALL426_ARCHIVE_MEMBER_BYTES_MATCH',members=426,server_extractions=0)))
