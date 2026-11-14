from pathlib import Path
import os, socket, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldD_seed0_train_20261113_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/launch_attempt_S_D_v1.json')
assert not out.exists() and (not claim.exists()) and (not any((x.is_symlink() for x in (claim, *claim.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_S_foldD_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/authorization_S_D_v1.json', 'c0ea959105bcfd6f5c9f3e70213fd67e5869fea9ba032df85c3f447a5e880a82'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/runtime_S_D_v1.json', 'ac22182ba7c1c83d6b84971cd4f7f1a256a948b23cc9ef64920c58817b1f34ae'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/launch_once_S_D_v1.sh', 'bffed63e21303b0e3a552a5e8320f00c51261e0bbd40f4571ef216214f1a6544')]:
    path = Path(p)
    assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='6c1e09d3366874f4f775061d9a957e1b5048dba0f295ff1127194bb798a90072'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_S_foldD_20261113_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_D_v1/launch_once_S_D_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', GPU=a, session='bcsp_scq_S_foldD_20261113_v1')))