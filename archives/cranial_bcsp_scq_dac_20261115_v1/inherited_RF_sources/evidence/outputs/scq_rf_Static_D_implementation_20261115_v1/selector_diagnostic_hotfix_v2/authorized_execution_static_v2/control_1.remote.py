from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/control/runtime_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzDtOxDAUQNE+q4hSY+mN/57NoPczcTEZxnYoQOwdRjT0956vZV23wbvecLuuG/F4N4MfplczO7ajHW+mn8dsNzUfl+3lmXd9nDrm69jRhvjciiRkH4oWLLGwi1JjEkFVz4EBEdlyzOSsFa4hQ0kcfA2FET1Y+nPxnPu9t0+c7X7806Pm5FGSZgvkrUciKJforNCvTZQcxhQQgSFT1RRq9VAFVLw4KGFbvpcfT4hE7g=='))
assert hashlib.sha256(b).hexdigest() == '1e953e2538260e29b124bc17aca1354a84dd66bf02dbb128ebde60414d36eb08'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '1e953e2538260e29b124bc17aca1354a84dd66bf02dbb128ebde60414d36eb08'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))