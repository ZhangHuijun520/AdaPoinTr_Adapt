from pathlib import Path
import importlib.util, json, hashlib, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_training_entry_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '44dc22ff01642c2347bf8a077a09381504f71dff858c92f193239ab2b8c99328'
s = importlib.util.spec_from_file_location('scq_installed_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def record(path, digest):
    p = Path(path)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=digest)
r = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldC_training_execution_request_v2.json', '95d6dfdb07a0e64a8f80646c65f84da38ff7297344e74541000fe1dbcc899b84'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_v2/authorization_v2.json', 'b95dce8e8f8131e61905e861c443b21ccd17ff9d948c118083d458b81a9b5c82'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_v2/runtime_v2.json', '687769d89975a3803bbf2480f644e0ba24e17fb7d22b9dadbdfe7880779e8ee2'))
assert len(r[3]) == 315 and r[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_METADATA_PASS', cases=315, updates=3900, model_calls=0)))