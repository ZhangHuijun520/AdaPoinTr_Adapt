from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzLtOAzEQheF+n2LlGku+jr28DJrxjFkX2RDbS0GUdydAQ3mk/3z3ZV3VKLtcUL2uisr40KPcdK96dmxHO951P4/ZLqI/rXr5ybvcThnzbezoIvze8saOMtsqCJ5KCZVMSJmLBHbZY0wElFIgoVQKpyomGF+eyxIw/Ll4zv3a2xfOdj3+6Tm4VCnajRMEAO/dE0oONx9Boli2SFt1lSCSYWvZFW+qQUhssEpWy2P5BkcaRGc='))
assert hashlib.sha256(b).hexdigest() == 'bd126d45c3ab52e31d38bf660fdb4bc1cf811d96eb230a09b8ecb32fdd2f2733'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bd126d45c3ab52e31d38bf660fdb4bc1cf811d96eb230a09b8ecb32fdd2f2733'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))