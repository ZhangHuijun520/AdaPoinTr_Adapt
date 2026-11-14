from pathlib import Path
import os, socket, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/launch_attempt_v1.json')
assert not out.exists() and (not claim.exists()) and (not any((x.is_symlink() for x in (claim, *claim.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_B_foldC_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/authorization_v1.json', '1d6ad8f2f28b0cd04cf963d14b749b52dfeca03d917af6e936987d13adcea17c'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/runtime_v1.json', 'c3d471d395ccb9cc725474b3bd08eb211e8e8755374d935559b8f7beeff5a9d0'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/launch_once_v1.sh', '8c1159f7d98bb4c7bdb3f4fc3910272c2b0518746b9d663c1154490e5e0163e8')]:
    path = Path(p)
    assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='132ea92fde3fb871f4bad6d78d18d625fc83c85e9e2719d52ef7cd2b9c3b9396'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_B_foldC_20261113_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control/launch_once_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', GPU=a, session='bcsp_scq_B_foldC_20261113_v1')))