from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_RF_ten_memory_execution_request_v1.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == '51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'
q = json.loads(qp.read_bytes())
import tarfile
c=json.loads((O/'completion.json').read_bytes());rs={r['name']:r for r in c['archive']['members']}
assert len(rs)==len(c['archive']['members'])==15
with tarfile.open(O/'development_predictions_v1.tar.gz') as t:
 ms=t.getmembers();assert len(ms)==15 and {m.name for m in ms}==set(rs)
 for m in ms:
  assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and m.size<8388608
  b=t.extractfile(m).read();r=rs[m.name];p=O/m.name
  assert p.is_file() and len(b)==r['bytes']==p.stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),m.name
print(json.dumps(dict(status='ALL15_ARCHIVE_MEMBER_BYTES_MATCH',members=15,server_extractions=0)))
