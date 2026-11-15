from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_authorization_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0E1JLUvNyS/ITc0r0U0sLcnIL8qsSizJzM/TLTNU0gFpKEotLE0tLokvzkg0MjUDaTRNSTFKSUxMNbcwNjQ2TjE0MTUzMDVJNDYzSjY2tTQ3t0w0sjQwNk5OtjRKSzJMNk01NzdNSzRMTjIxTTO2TLGEmJtaUZCTmZxZEl9anFoUj2I30JKSotJUsDJM2fiS1IoSkDueT1nxrGP784XrXqxb8nT7pic7up7sWfB+T8/T3qnPu9c86+t4NrcZJLij4dnchU/X9TybuiXYwxHoiafrdz7dNeX5rJYnO3pfLGt7Pnva03WdLxa3PtnR93TKeqB6kJY1C82MDYCkH9DSstSXi1qebe1+v2c2sjnv98yiOCy4arkAnD6pgA=='))
assert hashlib.sha256(b).hexdigest() == 'f2eb8524530bda209dd065bcfa5a1c3dfd9d46911b06f344a95b880313ceaa6e'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f2eb8524530bda209dd065bcfa5a1c3dfd9d46911b06f344a95b880313ceaa6e'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))