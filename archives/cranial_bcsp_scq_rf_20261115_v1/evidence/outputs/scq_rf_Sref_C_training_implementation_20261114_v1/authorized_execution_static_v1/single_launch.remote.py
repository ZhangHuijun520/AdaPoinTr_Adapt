from pathlib import Path
import socket, os, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_Sref_C_train_20261114_v1'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (path, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/authorization_v1.json', '9bd97cbef4a2d0be6f34fb3b745f44974a574cc44396f8fa18e7f2be261c13b1'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/runtime_v1.json', '19823a181641c98f710b5804e24aad4a6b1bdb5fe42f11a2bf2de40bbb7fc76b'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/launch_once_v1.sh', '4a688e674e27223cf6566544bac3184ec3a9a25e2c89f3d6899b58c1b2eb02f0')]:
    p = Path(path)
    assert not any((x.is_symlink() for x in (p, *p.parents))) and hashlib.sha256(p.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='6d63c000de45f02cee7e7318abedaef0bb96b39e32a5e0ae6f40bdfbf2c67b21'), f)
r = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_Sref_C_train_20261114_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/launch_once_v1.sh'])
assert r.returncode == 0
print(json.dumps(dict(status='SINGLE_RF_SREF_C_TRAINING_SUBMITTED', session='bcsp_scq_rf_Sref_C_train_20261114_v1', GPU=a)))