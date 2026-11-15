from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlUDtLw1AU3vsrQmYLN+/Wzc3JxR8QbpITGujL5CYURRCsUu1jah1aCqaKOJQURGmU/JzcJE75CybFQXF0OcP5nuecVRiGdfQGtDC7z7Ca7nSrBnjQ7HRb0CZV7JJGx7ZOMbE67arHsXulwIYTFxyiOg3MS/JOKCFBE2sK8GAIGCFNRiJCJg8Kp9drmDckuS5whmaYvIQVxTSFElI00TQ5kORvX+h1m5ZuEdV1wFZ/ZRchxHZhR/uLqgR6pOyRTp+TwTb1gyx4pNuXOLyNo/s8GtHxLB2uk8kgWV6Wy/AiWfo0GCWz1+PDg+IIunmnH9N03o/DcfZ0nS7uaHCTPVzF4YRONwW/lKx9WUDFPCpCPfhc9ZO3YR4tfvrk0fzfv6icV74ABbmqHA=='))
assert hashlib.sha256(b).hexdigest() == '56ef2d970f5b384018b48df1e7bb813d91ef4b46f191ef14d1cacbb8764cda49'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '56ef2d970f5b384018b48df1e7bb813d91ef4b46f191ef14d1cacbb8764cda49'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))