from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjb1uwyAQgHc/heW5SMedOSAvUx0crhniNIA7JOq7t1GX7t/Pc5rnpee9XGW5zEvK/dP0fDdtM6NJPerxYdp5jHot5ssuby+8lftZ+njvu6DjlxZCEKVkxdmoyEki+ARseaXCgCJbWVE3KADA2SswsOKKJYrLAPrXlXPst1YfMurt+FfXNai3yYlkjJ41qKOETOQz0hbEo/c5oVMRYE+JLGWhaH+fYEnjMn1PP25zQlY='))
assert hashlib.sha256(b).hexdigest() == '851f17a8812e3c7cef3e72cf576f365c4ccf87485ff2edde3ce4dd627334e097'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '851f17a8812e3c7cef3e72cf576f365c4ccf87485ff2edde3ce4dd627334e097'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))