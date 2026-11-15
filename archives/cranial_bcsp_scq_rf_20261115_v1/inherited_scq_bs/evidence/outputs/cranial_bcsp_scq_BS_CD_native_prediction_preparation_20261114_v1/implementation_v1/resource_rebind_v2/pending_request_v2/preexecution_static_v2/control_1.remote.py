from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_runtime_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjc1ugzAMgO88Bcp5SIkTkrgvM9mJLZAGdBB6WNV3H9Uuu38/z67vzVEmWcjcesPluA9VHvK13RdZ27Cfa5sXGR7OfLzRXb5POdrnMRGM8a0UCRw4JiBARB8SuGrZqlMGEAJfxXEJTitiVsUgzvqYVZywyEh/XTrbtO3zD7V5W//V7ZgEr4PH7KCQjMik16lWBfSZrwqFCkWTc94GAuWcJUeJnOIlmu7V/QLzUENJ'))
assert hashlib.sha256(b).hexdigest() == 'f49b1980e1efb3d0248ddf0581228d7f1a9244f80158b076a9dbd162b523e042'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f49b1980e1efb3d0248ddf0581228d7f1a9244f80158b076a9dbd162b523e042'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))