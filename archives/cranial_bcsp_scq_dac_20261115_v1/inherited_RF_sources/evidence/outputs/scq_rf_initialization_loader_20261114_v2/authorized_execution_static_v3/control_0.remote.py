from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/authorization_v3.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStNNLk1J1E0sLcnIL8qsSizJzM/TLTNU0gFpKEotLE0tLokvzkg0MjUDabRINE4xMDQ3Tks0Tk5Ntkw1NzZPNbYwSbZMTLO0TANyLC3Nks0tU9OMU80MkpJMgfwkQ5OUZCNz0zSj5MRkiLmpFQU5mcmZJfGlxalF8Sh2Ay0pKSpNBSvDlI0vSa0oAbnj6fZNT3Z0Pdmz4P2enqe9U593r3nW1/FsbjNQ8MX+DU8ndzzd0fO4oQmkZkf3s2ntT9f1PJu6JdjDEeiP93tmUewNrlouADCNgAA='))
assert hashlib.sha256(b).hexdigest() == 'f720da27fec89a92ca737b98d4105bfbada5465fc3fc65d8c32e980fb7bf90c5'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f720da27fec89a92ca737b98d4105bfbada5465fc3fc65d8c32e980fb7bf90c5'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))