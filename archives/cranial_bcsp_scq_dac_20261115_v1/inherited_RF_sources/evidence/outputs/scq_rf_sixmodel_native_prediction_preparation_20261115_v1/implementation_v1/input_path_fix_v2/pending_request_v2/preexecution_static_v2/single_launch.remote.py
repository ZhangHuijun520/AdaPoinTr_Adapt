from pathlib import Path
import socket, os, subprocess, hashlib, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v2')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/attempt_claim_v2.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_six_native_20261115_v2'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-383d118a-368c-94e3-166a-cad3efab8fd7', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_authorization_v2.json', 'f2eb8524530bda209dd065bcfa5a1c3dfd9d46911b06f344a95b880313ceaa6e'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_runtime_v2.json', '7053851f0aa1eeff3fcdd0ae58a83ddbaf5ed658cfd3dc496ad4d1669ffc350b'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_launch_once_v2.sh', 'a883611930516b5a70311781964fc818c3438ee92c515be0bf961f38817b8459')]:
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h and (not Path(p).is_symlink())
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_six_native_20261115_v2', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_launch_once_v2.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', session='bcsp_scq_rf_six_native_20261115_v2', forwards=630)))