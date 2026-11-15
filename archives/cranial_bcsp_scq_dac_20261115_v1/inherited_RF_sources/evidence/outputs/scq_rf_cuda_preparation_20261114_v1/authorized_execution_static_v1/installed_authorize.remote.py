from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_cuda_admission_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'a46c10023766933581f7113141db4e31a5c8fb47c107ece82901cdc58cc8dc47'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())
q = bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/SCQ_RF_artificial_cuda_execution_request_v1.json', '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32')
m.authorize(q, '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/control/authorization_v1.json', '6037f1f779a1410b1dc55c17ad9496bf02394859ee4b52735734e986165dcde9'), '6037f1f779a1410b1dc55c17ad9496bf02394859ee4b52735734e986165dcde9', bound('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/control/runtime_v1.json', '7f4fcc215d90aa2b04f010436817f4ba086e2dbaa120dba1baf5a89df07f80b2'))
assert q['science']['full_forward'] == 5 and q['science']['full_loss'] == q['science']['full_backward'] == 4
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))