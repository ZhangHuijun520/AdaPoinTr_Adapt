from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzEFuxCAMQNF9ThFlXaSAwZBepjK2aVhMpgOki1a9ezPqpvv/3/c0z0vnXW+0vM5L5v5hOj9MK2Y0qkc93k07j1Fvaj7t8vLMmz5O7eOt7+QCPjdPcSsYJbK6LfsA4EG2rMIuJm9XWMUzOgeaYy66OgEqVuxVXJ/Kn0vn2O+tftGo9+OfnqIGQUBFdRRSDrxZlgApSk6OL6GgdQS5JC/RWwUIYbWZkRQL4TL9TL/wX0Qe'))
assert hashlib.sha256(b).hexdigest() == '0294d7563568f18c87b4f59c2f272ec806818905dcf2699fb5e6f57e02458228'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '0294d7563568f18c87b4f59c2f272ec806818905dcf2699fb5e6f57e02458228'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))