from pathlib import Path
import importlib.util, json, hashlib, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_foldD_training_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '5c425e93616b614d3b67251c6f7f0bac2e2f7ec333bb4a453bd191fb8f22d718'
s = importlib.util.spec_from_file_location('scq_installed_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def record(path, digest):
    p = Path(path)
    return dict(path=str(p), bytes=p.stat().st_size, sha256=digest)
r = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_S_FoldD_training_execution_request_v1.json', '6c1e09d3366874f4f775061d9a957e1b5048dba0f295ff1127194bb798a90072'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/authorization_S_D_v1.json', 'c0ea959105bcfd6f5c9f3e70213fd67e5869fea9ba032df85c3f447a5e880a82'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/runtime_S_D_v1.json', 'ac22182ba7c1c83d6b84971cd4f7f1a256a948b23cc9ef64920c58817b1f34ae'))
assert len(r[3]) == 315 and r[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_METADATA_PASS', cases=315, updates=3900, model_calls=0)))