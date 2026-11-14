from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_authorization_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0E1JLUvNyS/ITc0r0U0sLcnIL8qsSizJzM/TLTNU0gFpKEotLE0tLokvzkg0MjUDaUxONUkySTIzN0o0srS0NDYxNzJMMUgySDNMSzIySk00Mk5JNUxKNjFMS7G0tEhLszRJNTQwNrNISzVMTUpNNU2EmJtaUZCTmZxZEl9anFoUj2I30JKSotJUsDJM2fiS1IoSkDueT1nxrGP784XrXqxb8nT7pic7up7sWfB+T8/T3qnPu9c86+t4NrcZJLij4dnchU/X9TybuiXYwxHoiafrdz7dNeX5rJYnO3pfLGt7Pnva03WdLxa3PtnR93TKeqB6kJY1C02MDICkH9DSstSXi1qebe1+v2c2sjnv98yiOCy4arkA/Xarrw=='))
assert hashlib.sha256(b).hexdigest() == '057e9e4b39812cae59bafa29ddf2938be1ea4d2cf711304a2fb88e86e6b769e4'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '057e9e4b39812cae59bafa29ddf2938be1ea4d2cf711304a2fb88e86e6b769e4'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))