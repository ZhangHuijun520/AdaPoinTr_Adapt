from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNpNzEGKwzAMQNF9TlGynoAlS3bUyxTZlkkWaaiTDExL7z6Ebrr7i8d/dZdLv+XJFu2vZz2GVofFlrX9De247/Niwy/0P6dr9jhs22/bpMjh9AxmYoQpo2TxzmGKkEciSSxWgIi9WgqFYy6KhCNHc8S5sA9C/PnqsU9rm5+6z+v9646eMyhHUAhlLFAtcvASlRNVcZDIOCauldiQkkUs6KoZWGUOWfru3f0DE3BANA=='))
assert hashlib.sha256(b).hexdigest() == '4457700eecf38cde42eb90034f918209c0baf75152332d01278c481fd48f54f0'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '4457700eecf38cde42eb90034f918209c0baf75152332d01278c481fd48f54f0'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))