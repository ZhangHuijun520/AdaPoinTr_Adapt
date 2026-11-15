from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/bcsp_scq_rf_Requery_D_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '0a99d7ca7542b5ab5d4db4787d6ae2ad30e38b5f2d8f764292102b0c984e0c44'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json', '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/control/authorization_v1.json', '87e5d636e6e2a58b5c91cd5387db82c9f6f612a3bf84d741e335501bc6ae6fa6'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/control/runtime_v1.json', '0294d7563568f18c87b4f59c2f272ec806818905dcf2699fb5e6f57e02458228'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))