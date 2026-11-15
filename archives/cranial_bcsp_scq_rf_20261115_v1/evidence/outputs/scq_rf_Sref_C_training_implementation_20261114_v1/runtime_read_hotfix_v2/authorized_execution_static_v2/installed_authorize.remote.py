from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/bcsp_scq_rf_Sref_C_training_entry_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '5a88b3ada34fe3f919166d73069d2831db2ccc365669444714a70757d7d39866'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/SCQ_RF_Sref_C_training_execution_request_v2.json', 'b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/authorization_v2.json', '9b059bd192aebaadbea26fc654b623082bd84d9aa69560c83b4cc347a3ac1664'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/runtime_v2.json', 'bd4627fb0fc97a4c6d4036b9bf3ea123d458d09b86b512c5858d718abdf60354'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))