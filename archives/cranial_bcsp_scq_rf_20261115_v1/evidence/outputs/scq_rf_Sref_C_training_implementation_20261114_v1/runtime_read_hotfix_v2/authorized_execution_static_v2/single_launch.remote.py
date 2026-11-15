from pathlib import Path
import socket, os, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v2')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/attempt_claim_v2.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_Sref_C_train_20261114_v2'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (path, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/authorization_v2.json', '9b059bd192aebaadbea26fc654b623082bd84d9aa69560c83b4cc347a3ac1664'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/runtime_v2.json', 'bd4627fb0fc97a4c6d4036b9bf3ea123d458d09b86b512c5858d718abdf60354'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/launch_once_v2.sh', 'e4380ba6346d6637cf568134f0b9f88fcb3e0c4ce0086ab9758d14015dac75cc')]:
    p = Path(path)
    assert not any((x.is_symlink() for x in (p, *p.parents))) and hashlib.sha256(p.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1'), f)
r = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_Sref_C_train_20261114_v2', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/control/launch_once_v2.sh'])
assert r.returncode == 0
print(json.dumps(dict(status='SINGLE_RF_SREF_C_TRAINING_SUBMITTED', session='bcsp_scq_rf_Sref_C_train_20261114_v2', GPU=a)))