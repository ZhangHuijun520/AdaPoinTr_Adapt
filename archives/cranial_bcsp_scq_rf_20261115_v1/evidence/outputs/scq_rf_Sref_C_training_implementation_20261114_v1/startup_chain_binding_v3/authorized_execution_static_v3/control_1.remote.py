from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/runtime_v3.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzLtuxCAQheHeT2FRB4mLGWbyMtEAQ0yx3izgFIny7vEqTU79n+97WVc18i43Vq+rSnl86JEfulc9O7ejHe+6n8dsN9GfVr088y6PU8Z8Gzu7AM8b+GiYECOST8GaTAGDAQuSADZLSOist6VCLEGIDbBEFyolBMOIfy6fc7/39sWz3Y9/eip1w824yBwvbmNfxdaYEZCkQCZTnBOxDi/fILrkr0HAYiULFbX8LL/HQ0GD'))
assert hashlib.sha256(b).hexdigest() == '999199588332093163fbb1823784114fca841352fff776b02abbb9e146fafbf5'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '999199588332093163fbb1823784114fca841352fff776b02abbb9e146fafbf5'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))