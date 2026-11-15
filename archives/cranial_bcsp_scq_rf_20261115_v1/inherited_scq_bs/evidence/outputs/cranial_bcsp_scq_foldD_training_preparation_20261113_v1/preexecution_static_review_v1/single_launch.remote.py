from pathlib import Path
import os, socket, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/launch_attempt_B_D_v1.json')
assert not out.exists() and (not claim.exists()) and (not any((x.is_symlink() for x in (claim, *claim.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_B_foldD_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/authorization_B_D_v1.json', 'a45e8318bac095c4a7b4b87a230c974f89f5584f51e119c31398b7522ef28c79'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/runtime_B_D_v1.json', 'ad884af5b901824a22cd9b99ce31ee1dbd5383ba8307a8f21f35703ef5331534'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/launch_once_B_D_v1.sh', '7c2f7cc698db17251dc6d670cfadaeb1854ac1d2375dfae307c426b6482ad3f6')]:
    path = Path(p)
    assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_B_foldD_20261113_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/launch_once_B_D_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', GPU=a, session='bcsp_scq_B_foldD_20261113_v1')))