from pathlib import Path
import socket, hashlib, json, importlib.util
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/bcsp_scq_rf_Static_D_training_entry_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'ef1e432b31d1db10a7cf03d9c962cfb9b259704e63a1e2b2d2b7404adac3c3aa'
s = importlib.util.spec_from_file_location('rf_installed_contract_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def bound(path, digest):
    p = Path(path)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    return json.loads(p.read_bytes())

def record(path, digest):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=digest)
result = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/SCQ_RF_Static_D_training_execution_request_v2.json', '9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/control/authorization_v2.json', '6e874ad7e820b424abb091632dbc0abb73a675aa0c08bfe75ff40fd0ed4d3095'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/control/runtime_v2.json', '1e953e2538260e29b124bc17aca1354a84dd66bf02dbb128ebde60414d36eb08'))
assert len(result[3]) == 315 and result[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', model_calls=0)))