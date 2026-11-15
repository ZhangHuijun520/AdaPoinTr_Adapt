from pathlib import Path
import socket, os, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldC_seed0_train_20261114_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_Requery_C_train_20261114_v1'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (path, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/authorization_v1.json', '51d903e79720830a4430e9a2d80c2cb457684a8cfdbe2c3b45f701c34914515c'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/runtime_v1.json', 'ba8c3b984672dfc4eeb9e6f5b2d03d7fd34ff533531e8c722f60ffed27b758f9'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/launch_once_v1.sh', 'f2fb1523525129e8678267117f5184ea4945c37f4c00aaf25a00eacc874218b4')]:
    p = Path(path)
    assert not any((x.is_symlink() for x in (p, *p.parents))) and hashlib.sha256(p.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'), f)
r = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_Requery_C_train_20261114_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/launch_once_v1.sh'])
assert r.returncode == 0
print(json.dumps(dict(status='SINGLE_RF_REQUERY_C_TRAINING_SUBMITTED', session='bcsp_scq_rf_Requery_C_train_20261114_v1', GPU=a)))