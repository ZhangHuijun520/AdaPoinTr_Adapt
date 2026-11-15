from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStNNLk1J1E0sLcnIL8qsSizJzM/TLTNU0gFpKEotLE0tLokvzkg0MjUDabQwtTA1STMyMU4xsjQwMEhONk80SE21ME8yME4zSU41MrY0N0lLtjRKsTRJMUtLMTG3TEsxszRNNbMAqkwyNoKYm1pRkJOZnFkSX1qcWhSPYjfQkpKi0lSwMkzZ+JLUihKQO55u3/RkR9eTPQve7+l52jv1efeaZ30dz+Y2AwVf7N/wdHLH0x09jxuaQGp2dD+b1v50Xc+zqVuCPRyB/ni/ZxbF3uCq5QIAGkd+Dg=='))
assert hashlib.sha256(b).hexdigest() == '6037f1f779a1410b1dc55c17ad9496bf02394859ee4b52735734e986165dcde9'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '6037f1f779a1410b1dc55c17ad9496bf02394859ee4b52735734e986165dcde9'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))