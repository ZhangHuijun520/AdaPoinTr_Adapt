from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/bcsp_scq_rf_Sref_D_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'c990e9446cc30ddda100dd60c5a991b3bad5263dcb0ae6baab97aefe8de11fbc'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/SCQ_RF_Sref_D_training_execution_request_v1.json', '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/authorization_v1.json', 'd48d71b5aac2976d8d53b26337c23f8a7277cb25daa0673b313ca391e42013d9'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/runtime_v1.json', '851f17a8812e3c7cef3e72cf576f365c4ccf87485ff2edde3ce4dd627334e097'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))