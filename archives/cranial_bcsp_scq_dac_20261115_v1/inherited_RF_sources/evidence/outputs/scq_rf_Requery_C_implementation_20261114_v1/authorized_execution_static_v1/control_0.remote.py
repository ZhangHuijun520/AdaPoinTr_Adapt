from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2k2Mk9NM01MTDRMNgURyUYmZqkWySamppbmlhaGKQZGxsZmpoYpaUmJyWnmZkaGZsbmiRaJ5knGZuaJliaW5hBzUysKcjKTM0viS4tTi+JR7AZaUlJUmgpWhikbX5JaUQJyx9Ptm57s6HqyZ8H7PT1Pe6c+717zrK/j2dxmoOCL/Ruerut5NnXL08kdT3f0PG5oAqnc0f1sWjtEPNjDEeib93tmUewZrlouAF/0g+c='))
assert hashlib.sha256(b).hexdigest() == '51d903e79720830a4430e9a2d80c2cb457684a8cfdbe2c3b45f701c34914515c'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '51d903e79720830a4430e9a2d80c2cb457684a8cfdbe2c3b45f701c34914515c'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))