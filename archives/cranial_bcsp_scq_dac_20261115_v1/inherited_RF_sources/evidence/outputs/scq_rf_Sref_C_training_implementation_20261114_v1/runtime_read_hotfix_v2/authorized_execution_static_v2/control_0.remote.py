from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/authorization_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2s2tjBPNLBISjFKSTU1NzU3Mk6xSLOwTDRLM0g2T0syNDMzNbU0MDSwSE1NMUhNMzNKNjBIMbJIsjC2NEkxSYOam1pRkJOZnFkSX1qcWhSPYjfQkpKi0lSwMkzZ+JLUihKQO55u3/RkR9eTPQve7+l52jv1efeaZ30dz+Y2AwVf7N/wdHLH0x09jxuaQGp2dD+b1v50Xc+zqVuCPRyB/ni/ZxbF3uCq5QIAczZ/qQ=='))
assert hashlib.sha256(b).hexdigest() == '9b059bd192aebaadbea26fc654b623082bd84d9aa69560c83b4cc347a3ac1664'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '9b059bd192aebaadbea26fc654b623082bd84d9aa69560c83b4cc347a3ac1664'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))