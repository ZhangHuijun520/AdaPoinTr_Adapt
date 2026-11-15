from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2k2STS3TDMzTzFPTjWyTDIxNTY2MU6xTEpNSTYytzAxNDA2SDFJNjMyMk5NMk9KSzUwSjFOTDNMMQSqAOpLTYGYm1pRkJOZnFkSX1qcWhSPYjfQkpKi0lSwMkzZ+JLUihKQO55u3/RkR9eTPQve7+l52jv1efeaZ30dz+Y2AwVf7N/wdF3Ps6lbnk7ueLqj53FDE0jlju5n09oh4sEejkDfvN8zi2LPcNVyAQAPbIW9'))
assert hashlib.sha256(b).hexdigest() == '87e5d636e6e2a58b5c91cd5387db82c9f6f612a3bf84d741e335501bc6ae6fa6'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '87e5d636e6e2a58b5c91cd5387db82c9f6f612a3bf84d741e335501bc6ae6fa6'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))