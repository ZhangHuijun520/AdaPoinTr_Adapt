from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/authorization_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlT71Kw0Ac3/MUIbMH1/Mu13Rzc/cBwuX6PxJQ296HFEUQHSw2ukgdBMEHEBEpNEPAh7EX3foKJjqJo+vv+3cShGFkZA4HIhqEUSbNGBk5QVoh6YYCCWfzkS6OhS1Gh+ioF211Bg0TB8amJheExZ0RJ0OIMWWKgJQ8xoz18XYiiSSMEwoJBQGY9zNGFKdUgIqBMMYp4wx6mVQ/uTAd7xeysKkzoNNf3W2J1Q6+ZX/Z1MLUdjv86nVdXa3rx01d+uvFx/ypuZk1Dxct+Pn24m9nvirfz847TTVv7i79c9kslnu7O+2PTX3/7xvBafAF4w59kg=='))
assert hashlib.sha256(b).hexdigest() == '0324997a169380ebbd6a76c8bd878763911a7be207f15714c2cc1dadc3b50de9'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '0324997a169380ebbd6a76c8bd878763911a7be207f15714c2cc1dadc3b50de9'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))