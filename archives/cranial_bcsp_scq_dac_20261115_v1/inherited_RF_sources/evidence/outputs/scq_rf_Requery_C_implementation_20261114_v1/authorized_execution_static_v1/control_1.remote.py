from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjDFuxCAQRXufwqIOEgwMA7lMNIwhplhvFnCKRLl71kqT5hdP/73vZV3VkL3cWL2uKsv40EMeulc9O7ejHe+6n8dst6I/rXq57r08zjLm29gZMFwaUKnIzFbwGgEfShSPmChFuxlwLqDdamapFMAGRxyZsgvEySf66/I593tvXzzb/fhXf5rJuEKJwERn2HtnSmLYohGQ7JFC9BylbrmAuCeoZKw4n6xHi6KWn+UXdYZCJA=='))
assert hashlib.sha256(b).hexdigest() == 'ba8c3b984672dfc4eeb9e6f5b2d03d7fd34ff533531e8c722f60ffed27b758f9'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'ba8c3b984672dfc4eeb9e6f5b2d03d7fd34ff533531e8c722f60ffed27b758f9'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))