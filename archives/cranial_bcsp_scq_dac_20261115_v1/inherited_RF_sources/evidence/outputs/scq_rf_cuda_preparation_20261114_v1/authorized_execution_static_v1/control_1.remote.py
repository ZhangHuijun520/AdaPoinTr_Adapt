from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzD1uwzAMQOHdpzA0V4B+SFHMZQqJomAPSRrL7tAid4+DLt3f+36neTZDFr0Wc5lNlfFlhzzs1q0crdjtuO3rVe23Nx/vdNPHoWP/HEsJmN5LxozQA8QW2DknQsWpZqoudhANkQm6cGgMLfUGxL0lRk35LGsMf2459uW+rT9lX++3f3pykbrvRFw8eFd9E0TxVE6OU+3u9CEjq0LFQBEpgnJOPmGTpmym5/QC3ldAdw=='))
assert hashlib.sha256(b).hexdigest() == '7f4fcc215d90aa2b04f010436817f4ba086e2dbaa120dba1baf5a89df07f80b2'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '7f4fcc215d90aa2b04f010436817f4ba086e2dbaa120dba1baf5a89df07f80b2'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))