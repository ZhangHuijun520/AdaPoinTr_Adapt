from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/runtime_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjTuOwyAQQHufwqJeJBgYBvYy0TAMsov8jL1Fotx9N9om/fs8p3k2QxY9s/meTZVxs0PudutWjsZ2Oy77elb7483XG930fujYT2NhwPRWXGmaXMQOKkLJIWYXioAAEkQtUVkd5YrQKUbWnhQQKSKh+ir9v8vHvly39cH7er181gPEUoh9KiE7rbUlpiS5tkyZUijeM1UFR90j+fj3Fd+4SajomhYzvaZfynBA3w=='))
assert hashlib.sha256(b).hexdigest() == 'dd767335fe3255fdf0078217179b8c74974470749ee729ab7ba02c18f466c510'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'dd767335fe3255fdf0078217179b8c74974470749ee729ab7ba02c18f466c510'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))