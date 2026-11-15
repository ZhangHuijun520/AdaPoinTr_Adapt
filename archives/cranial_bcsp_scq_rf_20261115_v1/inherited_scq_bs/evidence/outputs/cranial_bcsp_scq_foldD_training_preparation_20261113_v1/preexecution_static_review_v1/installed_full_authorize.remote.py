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
r = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldD_training_execution_request_v1.json', '4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/authorization_B_D_v1.json', 'a45e8318bac095c4a7b4b87a230c974f89f5584f51e119c31398b7522ef28c79'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/runtime_B_D_v1.json', 'ad884af5b901824a22cd9b99ce31ee1dbd5383ba8307a8f21f35703ef5331534'))
assert len(r[3]) == 315 and r[1]['counts']['updates'] == 3900
print(json.dumps(dict(status='INSTALLED_FULL_AUTHORIZE_METADATA_PASS', cases=315, updates=3900, model_calls=0)))