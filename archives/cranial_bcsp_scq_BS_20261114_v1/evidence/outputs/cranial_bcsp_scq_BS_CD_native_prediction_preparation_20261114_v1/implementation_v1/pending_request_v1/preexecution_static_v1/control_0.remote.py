from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlkL9Kw1AUxvc8Rchs4OZ/6+bm5OIDhJvkSANtU5ObUBRBsEq1f6bWoaVgq4hDSUGURsnj5CZxyiuY6KI4upzhnO/7fuecU4ZlOc9sQAtzuyxnmF6HtyCAptNpQZvw2CcNx7VPMLGdNh8I3E5lcOHYB4/oXgOLiloZNRUJdQGDoWqyIkkgyYKlIQVZhlJDUh2woVqWqcmigDVNMo4k1UAK1ATVAoxEU/7OhW6naZs20X0PXP0Xu4QQ14cv2d+pTqBLqj2yyVPa32bLMA8f6PY5iW6S+K6Ih3Q0zQbrdNxPFxdVMzpPF0saDtPpy+H+XnkE3bzR90k26yXRKH+8yua3NLzO7y+TaEwnm1JfWdZLWURlPSihAXyseunroIjnP3OKePbvXzBnzCdn0alN'))
assert hashlib.sha256(b).hexdigest() == 'abca69f30d2b23ac65f9a3277805ab9031708d55d08218e436623ce2a72a6e58'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'abca69f30d2b23ac65f9a3277805ab9031708d55d08218e436623ce2a72a6e58'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))