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
q = bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/SCQ_RF_artificial_cuda_execution_request_v2.json', '09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf')
m.authorize(q, '09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/authorization_v2.json', '0324997a169380ebbd6a76c8bd878763911a7be207f15714c2cc1dadc3b50de9'), '0324997a169380ebbd6a76c8bd878763911a7be207f15714c2cc1dadc3b50de9', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/runtime_v2.json', 'dd767335fe3255fdf0078217179b8c74974470749ee729ab7ba02c18f466c510'))
assert q['science']['full_forward'] == 5 and q['science']['full_loss'] == q['science']['full_backward'] == 4
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))