from pathlib import Path
import os, socket, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/launch_attempt_S_C_v1.json')
assert not out.exists() and (not claim.exists()) and (not any((x.is_symlink() for x in (claim, *claim.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_S_foldC_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/authorization_S_C_v1.json', 'c22bafc024fa45c006a9c3186af7eccbe58a77b6abca81f671ca7e7afcaf88a6'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/runtime_S_C_v1.json', '8f537a9cc4bbf26f4099f54598a57d226f6896cffe1536355ac7ecac93d7b4f5'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/launch_once_S_C_v1.sh', 'ad04a71e039777a63b5d0b47b2d7f7cb4efa1df6b0e1855a14aadcb6bf18d2df')]:
    path = Path(p)
    assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_S_foldC_20261113_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/launch_once_S_C_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', GPU=a, session='bcsp_scq_S_foldC_20261113_v1')))