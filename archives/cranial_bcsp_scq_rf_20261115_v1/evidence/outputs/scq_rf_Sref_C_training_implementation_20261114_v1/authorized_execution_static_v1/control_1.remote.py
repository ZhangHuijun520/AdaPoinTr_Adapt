from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNjTtuwzAMQHefwvBcAfrQktXLFCRF1hriNJLcoUHu3gTo0P197tM8L513ueDyPi/E/ct0vpmmZjSsRz0+TTuPUS9ivt3y9sKb3E7p46Pv6Nf40mKJga21RWBV61kkSQpuQ5KCopYoRwpZgsdVLEpUsFSU1HNM5P+6eI792uoPjno9/tUzlZyYRAF9sfS0AygFSs8ZQE6AawJmgJCjbopuk6SexEfHLpBbpsf0C3Y3RR4='))
assert hashlib.sha256(b).hexdigest() == '19823a181641c98f710b5804e24aad4a6b1bdb5fe42f11a2bf2de40bbb7fc76b'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '19823a181641c98f710b5804e24aad4a6b1bdb5fe42f11a2bf2de40bbb7fc76b'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))