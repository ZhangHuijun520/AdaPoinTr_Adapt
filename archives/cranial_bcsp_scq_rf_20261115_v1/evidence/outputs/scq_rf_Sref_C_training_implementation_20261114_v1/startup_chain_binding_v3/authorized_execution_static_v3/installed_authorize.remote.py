from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'bc01d750489002949bd442bcd806e8340d272ce7dfe16727ede8ee54f15d4adf'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json', '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/authorization_v3.json', 'bdf484027aa76644a3fe1f7c8689ed6c90d22ee128f670882b3333658d1ece9d'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/runtime_v3.json', '999199588332093163fbb1823784114fca841352fff776b02abbb9e146fafbf5'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))