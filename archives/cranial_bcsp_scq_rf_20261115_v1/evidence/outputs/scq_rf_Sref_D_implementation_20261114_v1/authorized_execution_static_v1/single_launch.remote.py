from pathlib import Path
import socket, os, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_Sref_D_train_20261114_v1'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (path, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/authorization_v1.json', 'd48d71b5aac2976d8d53b26337c23f8a7277cb25daa0673b313ca391e42013d9'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/runtime_v1.json', '851f17a8812e3c7cef3e72cf576f365c4ccf87485ff2edde3ce4dd627334e097'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/launch_once_v1.sh', '0901af12e7c11e92e5c71a6aac71ac7b1be148ab4b3a243b078e652fdcf9d695')]:
    p = Path(path)
    assert not any((x.is_symlink() for x in (p, *p.parents))) and hashlib.sha256(p.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'), f)
r = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_Sref_D_train_20261114_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/launch_once_v1.sh'])
assert r.returncode == 0
print(json.dumps(dict(status='SINGLE_RF_SREF_D_TRAINING_SUBMITTED', session='bcsp_scq_rf_Sref_D_train_20261114_v1', GPU=a)))