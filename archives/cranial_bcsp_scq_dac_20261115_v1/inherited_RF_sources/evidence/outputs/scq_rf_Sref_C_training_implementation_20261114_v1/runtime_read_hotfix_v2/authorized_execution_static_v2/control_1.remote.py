from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/runtime_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjbluwzAMQHd/haG5AmidVH6mIEWp1hCnkeQOCfrvPdCh+zuey7qqkfdyJXVZFefxrke+61717NSOdrzpfh6zXYv+2NTLD97L/Sxjvo6djA+/msVIgCxGio8+GitYMVGokGPlLQTvE2yApQiUGkwGEIOMNjlx9a9L59xvvT1ottvxr54YfGLZkqHCRMKFTKg5eMfBWEDDgk4SUUg+QEbLLmfrIlnK32unls/lC7POQ3g='))
assert hashlib.sha256(b).hexdigest() == 'bd4627fb0fc97a4c6d4036b9bf3ea123d458d09b86b512c5858d718abdf60354'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bd4627fb0fc97a4c6d4036b9bf3ea123d458d09b86b512c5858d718abdf60354'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))