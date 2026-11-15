from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'c457800917fbecd3fd3e7c38f73cc1971806a905dd874ecad3d3f96da3f9755f'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json', 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/authorization_v1.json', 'bfa00d971bd19ef18b0fdd355834186706875053b334bd1ddfbe338e42d405f4'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/runtime_v1.json', '93c79a1cc0b3c330ec026b25eb077795a5d2cc15d2a634aa98af917f5d0365cd'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))