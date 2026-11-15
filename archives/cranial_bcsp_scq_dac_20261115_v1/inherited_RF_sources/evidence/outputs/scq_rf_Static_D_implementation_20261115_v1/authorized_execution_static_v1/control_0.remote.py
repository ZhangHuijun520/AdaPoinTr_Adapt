from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqr5lJQUCpOzkjNTVSyUlBKSi4u0C1OLtQtStMtKUrMzMvMS9dNLC3JyC/KrEosyczP0y0zVNIBaSpKLSxNLS6JL85INDI1A2u2sEwxSrJIMUxLTTQzTkpONklLMjAxt0hJTjVJMbIwTjQ1TzJLMjc3SUpNMk9OTjFPSzUwMTBOBvIMk8xSzCDmplYU5GQmZ5bElxanFsWj2A20pKSoNBWsDFM2viS1ogTkjqfbNz3Z0fVkz4L3e3qe9k593r3mWV/Hs7nNQMEX+zc8XdfzbOqWp5M7nu7oedzQBFK5o/vZtHaIeLCHI9A37/fMotgzXLVcABYKhz8='))
assert hashlib.sha256(b).hexdigest() == '8427fb519d7646633274b72a9356e5e1d1ab9f2fb65b0d11d2c30f0a67d0afe8'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '8427fb519d7646633274b72a9356e5e1d1ab9f2fb65b0d11d2c30f0a67d0afe8'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))