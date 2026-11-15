from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/runtime_v3.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjLsOwjAMAPd+RZWZSGnSPMzPINux1Q68mpYBxL9TxMJ40t29ur43jSc5ozn2hrjdbOO7XdTyVtEu22Wdz2Ifgzl81UXum7T11Cb0MX2TgqG6IQfFwMIgOWQJZWRABdAdABJnEA2SHFHcmYaxss9RPSP/vrit03WZn7jO18vfXbN3FX1W4QIIe7D/CUodBxdJCSvGMUXloJxiLRy8QHFKmRQcR9O9uw+sa0NE'))
assert hashlib.sha256(b).hexdigest() == '58e8e47b15ceee37cb23c019bab371a5e40879b6933ce799857c4affb0e26d03'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '58e8e47b15ceee37cb23c019bab371a5e40879b6933ce799857c4affb0e26d03'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))