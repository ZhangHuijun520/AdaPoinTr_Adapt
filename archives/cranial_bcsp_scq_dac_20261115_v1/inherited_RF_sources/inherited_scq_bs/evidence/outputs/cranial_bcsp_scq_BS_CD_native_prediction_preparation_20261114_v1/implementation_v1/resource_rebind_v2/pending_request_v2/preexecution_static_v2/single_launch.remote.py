from pathlib import Path
import socket, os, subprocess, hashlib, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_single_attempt_claim_v2.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_BS_CD_native_20261114_v2'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_authorization_v2.json', '057e9e4b39812cae59bafa29ddf2938be1ea4d2cf711304a2fb88e86e6b769e4'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_runtime_v2.json', 'f49b1980e1efb3d0248ddf0581228d7f1a9244f80158b076a9dbd162b523e042'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_launch_once_v2.sh', '3fe2dcf7c80b7626036d075184d381dc15b1bb77e5c5b2b8e5ef65deabc5686a')]:
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h and (not Path(p).is_symlink())
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_BS_CD_native_20261114_v2', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_launch_once_v2.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', session='bcsp_scq_BS_CD_native_20261114_v2', forwards=420)))