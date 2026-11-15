from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '26be687df4a74a71d45237402e91523750d8d089409d2e372c70ebef1d3c38f1'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/SCQ_RF_Requery_C_training_execution_request_v1.json', '27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/authorization_v1.json', '51d903e79720830a4430e9a2d80c2cb457684a8cfdbe2c3b45f701c34914515c'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/runtime_v1.json', 'ba8c3b984672dfc4eeb9e6f5b2d03d7fd34ff533531e8c722f60ffed27b758f9'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))