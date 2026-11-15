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
r = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_S_FoldC_training_execution_request_v1.json', '1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/authorization_S_C_v1.json', 'c22bafc024fa45c006a9c3186af7eccbe58a77b6abca81f671ca7e7afcaf88a6'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/runtime_S_C_v1.json', '8f537a9cc4bbf26f4099f54598a57d226f6896cffe1536355ac7ecac93d7b4f5'))
assert len(r[3]) == 315 and r[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_METADATA_PASS', cases=315, updates=3900, model_calls=0)))