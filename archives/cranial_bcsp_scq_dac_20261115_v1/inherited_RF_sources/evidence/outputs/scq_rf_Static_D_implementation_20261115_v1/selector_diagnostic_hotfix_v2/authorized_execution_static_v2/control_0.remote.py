from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/control/authorization_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlT79Kw0Ac3vMUIbMH8ZpLem7d3H2A8MsvF3OgaXt3kaIIooPFRhepgyC4uImCCGbI29iL3foKNnYSR9fv/3fiuK6nMReH4O24XoJ6RDSOicqIUSALWewTKE0+VPIYjBwW5Gjb2+pMSoxLoU2sc6As7Mw8jQADxgUHHnLshWkWRmkKQgTI0AcApBj2kx6lKWas7/MIWZAxjgCBT5NNrpiMDiRKE5daqPhX97rEqFL8yP6ysRET0+2wH2+L+mrRPK6ayl7Pv2bP7c20fbhYvj7Zl6qdv9vbqa2rz7PzTlbP2rvLDb63O1hfWTX3/37inDrfvm+EUg=='))
assert hashlib.sha256(b).hexdigest() == '6e874ad7e820b424abb091632dbc0abb73a675aa0c08bfe75ff40fd0ed4d3095'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '6e874ad7e820b424abb091632dbc0abb73a675aa0c08bfe75ff40fd0ed4d3095'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))