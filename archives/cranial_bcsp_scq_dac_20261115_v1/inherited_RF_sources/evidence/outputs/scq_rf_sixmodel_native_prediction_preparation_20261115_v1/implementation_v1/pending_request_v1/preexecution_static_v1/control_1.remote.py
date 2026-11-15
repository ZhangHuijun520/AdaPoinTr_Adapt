from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjUtuhDAQRPecAnkdJLf/nsuM2u5ugRRgAmYWiXL3QDSL2ZX06lX9dH2v9jryjOrWq1L3x0D85M/1MfPShu1Y2jTz8AT1cVU3/jp4b/d9ROPDv+K1LS5FNkwWtS5BO63FcISaExryIVugQmI8xihiLxSLEwH24bWLRxvXbfrGNq3L27oPLIZy1OKLTU5DOr/oNGMpCSxlYHHFBYErgSOoWE8Ug6uELqvut/sDhntCdQ=='))
assert hashlib.sha256(b).hexdigest() == '7a25572a9068db05f2db1427182f58e2bd4d62ea7624f0b862d0653c3343e416'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '7a25572a9068db05f2db1427182f58e2bd4d62ea7624f0b862d0653c3343e416'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))