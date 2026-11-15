from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlT79Kw0Ac3vMUIbOBX67JNXFzc/cBwi93F3OgaXt3kaIIooPFRhepgyD4ACJSBDMEfBib6NZXMLGTOLp+/78Ty7YdzTJxiM627SRMj13NJq5KXaNQ5jLfd7Ew2UjJYzRylLtHnrPVm5SYFEKbWGdIAtqbwzBEPkg8DLyIE5pgBMMEqEf9gaBAEFPhE56CAADKhhwoUE58IiIMGADf5Irp+EAyaeJCCxX/6u5KjCrEj+wvGxsxNf2O5m25qq5W9eO6Lpvrxef8qb2ZtQ8XHfj1/tI8l+3itbmdNVX5cXbeK6t5e3e5wfd2d7o36/r+32esU+sbDA+DkQ=='))
assert hashlib.sha256(b).hexdigest() == 'd48d71b5aac2976d8d53b26337c23f8a7277cb25daa0673b313ca391e42013d9'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd48d71b5aac2976d8d53b26337c23f8a7277cb25daa0673b313ca391e42013d9'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))