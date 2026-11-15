from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/bcsp_scq_rf_Static_D_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '20ad874ebb11c6b42f3d72399245a28c6936eef62e8d97491ad20d8bf1d733b6'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/SCQ_RF_Static_D_training_execution_request_v1.json', 'b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/control/authorization_v1.json', '8427fb519d7646633274b72a9356e5e1d1ab9f2fb65b0d11d2c30f0a67d0afe8'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/control/runtime_v1.json', 'bd126d45c3ab52e31d38bf660fdb4bc1cf811d96eb230a09b8ecb32fdd2f2733'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))