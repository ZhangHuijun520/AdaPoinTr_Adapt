from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2lONDYyN002s0w1t0izNE0xtTQ2tUhKtEg2MzJMNjNOTjIwNU4yNUmyNDcxM0+2MLUwTjUzT0tNTUkySjI0MDVMg5ibWlGQk5mcWRJfWpxaFI9iN9CSkqLSVLAyTNn4ktSKEpA7nm7f9GRH15M9C97v6XnaO/V595pnfR3P5jYDBV/s3/B0Xc+zqVueTu54uqPncUMTSOWO7mfT2iHiwR6OQN+83zOLYs9w1XIBABA3g7U='))
assert hashlib.sha256(b).hexdigest() == 'bfa00d971bd19ef18b0fdd355834186706875053b334bd1ddfbe338e42d405f4'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bfa00d971bd19ef18b0fdd355834186706875053b334bd1ddfbe338e42d405f4'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))