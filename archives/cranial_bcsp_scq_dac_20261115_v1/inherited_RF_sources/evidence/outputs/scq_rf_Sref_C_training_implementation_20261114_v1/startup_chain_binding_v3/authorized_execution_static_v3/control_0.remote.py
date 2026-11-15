from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/authorization_v3.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2k2MzY3SLS0sDC3sDROMjU0SLY0tTA1MDM0S00yMzMxtLSwtDAyNDZMSTMzTzFNtUw0MEtMNTcyTbNMsjAzSLSwgJibWlGQk5mcWRJfWpxaFI9iN9CSkqLSVLAyTNn4ktSKEpA7nm7f9GRH15M9C97v6Xm6fieQ/WL/hqfrep5N3fJ0csfTHT1Pe6c+717zrHP5i4U9z/o6ns1tftzQBNKyo/vZtHaIymAPR6C33u+ZRbGvuGq5AJ2Ah7E='))
assert hashlib.sha256(b).hexdigest() == 'bdf484027aa76644a3fe1f7c8689ed6c90d22ee128f670882b3333658d1ece9d'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bdf484027aa76644a3fe1f7c8689ed6c90d22ee128f670882b3333658d1ece9d'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))