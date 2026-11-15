from pathlib import Path
import importlib.util, json, hashlib, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd073deab9a21c4dd3ffb3f8fdf05332c73196f260ce2bbb0f7b577a09efde53d'
s = importlib.util.spec_from_file_location('scq_installed_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def record(path, digest):
    p = Path(path)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=digest)
r = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldC_training_execution_request_v1.json', '132ea92fde3fb871f4bad6d78d18d625fc83c85e9e2719d52ef7cd2b9c3b9396'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/authorization_v1.json', '1d6ad8f2f28b0cd04cf963d14b749b52dfeca03d917af6e936987d13adcea17c'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/runtime_v1.json', 'c3d471d395ccb9cc725474b3bd08eb211e8e8755374d935559b8f7beeff5a9d0'))
assert len(r[3]) == 315 and r[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_METADATA_PASS', cases=315, updates=3900, model_calls=0)))