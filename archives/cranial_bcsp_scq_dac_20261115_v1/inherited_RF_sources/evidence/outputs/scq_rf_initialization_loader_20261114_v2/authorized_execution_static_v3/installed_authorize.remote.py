from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())
q = bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/SCQ_RF_artificial_cuda_execution_request_v3.json', '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac')
m.authorize(q, '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/authorization_v3.json', 'f720da27fec89a92ca737b98d4105bfbada5465fc3fc65d8c32e980fb7bf90c5'), 'f720da27fec89a92ca737b98d4105bfbada5465fc3fc65d8c32e980fb7bf90c5', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/runtime_v3.json', '58e8e47b15ceee37cb23c019bab371a5e40879b6933ce799857c4affb0e26d03'))
assert q['science']['full_forward'] == 5 and q['science']['full_loss'] == q['science']['full_backward'] == 4
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))