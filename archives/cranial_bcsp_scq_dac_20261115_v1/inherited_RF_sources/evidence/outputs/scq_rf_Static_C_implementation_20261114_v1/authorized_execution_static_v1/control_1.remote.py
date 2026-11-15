from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzbtuAyEQheF+n2JFHSRgGC55mYiBIUvhdQysC0d593jlxv1/vvO7rKsYeeNLEp+roDx+5Mg32aucPbW97d+yH/tsF5Z3LT7OvPPt4DG/xpYMunOWwHjMLrIPNWLBCBgoheyMzg4yKQRCS9Fb53PAAOx8ZS5kSCvU9eWmY27X3h5ptuv+plNNSpXoNRUduepAqpYC+HSsDs4rFzyeFwD2mZRSiQECW1OswmrF8rf8A3QTQqE='))
assert hashlib.sha256(b).hexdigest() == '93c79a1cc0b3c330ec026b25eb077795a5d2cc15d2a634aa98af917f5d0365cd'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '93c79a1cc0b3c330ec026b25eb077795a5d2cc15d2a634aa98af917f5d0365cd'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))