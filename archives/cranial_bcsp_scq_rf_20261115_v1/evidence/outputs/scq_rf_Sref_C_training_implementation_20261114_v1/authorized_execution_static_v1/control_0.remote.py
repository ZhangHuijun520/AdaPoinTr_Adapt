from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlT79Kw0Ac3vMUIbMH10tzsW7d3H2AcHf5nTnQtL27SFEE0cFio4vUQRB8ABEpghkCPkx70a2vYCIu4uj6/f9OPN8PjMjgkAU7fsCFGSMjJkhLZDVTucr3EStsNtLqmFk1ytFRL9jqTBomBRibmIyRiHZmmtJQYIxT6EcSEwEQQxz2thmHlIHEnA8oDwcQEhYBZkBlH/NUckkEjTn5yYXp+EAJZZPCgE5+dbclVhfwLfvLJhamttvh3pbr6mpdP27q0l0vPuZPzc2sebhowc/3F3c7c1W5OjvvNNW8ubt0z2WzeN3bHbY/NvX9v294p94X/2uCvQ=='))
assert hashlib.sha256(b).hexdigest() == '9bd97cbef4a2d0be6f34fb3b745f44974a574cc44396f8fa18e7f2be261c13b1'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '9bd97cbef4a2d0be6f34fb3b745f44974a574cc44396f8fa18e7f2be261c13b1'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))