from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzD1uwzAMQOHdpzA01wBFipSUyxSURMMGajv1T4YGuXsRdOn+3vfs+t4ddbJF3a13pR73odnDvrb7Yus57Nd6zosND+8+3ulu35cd5+cxKbK8lyjgs1crEgMTGQXfIjC0wgkomxZprcaAXmOkMpIUYEtemilgDX+uXue07fOPnvO2/tO1VJU8EjQsSFqFx6yEMSZgLRnIR0iNuUFCnyyQCFI11Igqxsl1r+4XOdZA2g=='))
assert hashlib.sha256(b).hexdigest() == 'd710dabeacfcdd16a0f894993c9f1e95921c5af6522ac06d4df5e8a5d9964806'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd710dabeacfcdd16a0f894993c9f1e95921c5af6522ac06d4df5e8a5d9964806'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))