from pathlib import Path
import socket, os, subprocess, hashlib, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_single_attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_BS_CD_native_20261114_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_authorization_v1.json', 'abca69f30d2b23ac65f9a3277805ab9031708d55d08218e436623ce2a72a6e58'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_runtime_v1.json', 'd710dabeacfcdd16a0f894993c9f1e95921c5af6522ac06d4df5e8a5d9964806'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_launch_once_v1.sh', 'ca470768504dc370693c9285cf723e70f5759ed7963a84c1a68a62b216d40f01')]:
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h and (not Path(p).is_symlink())
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='760191aeb674533e341d7050db58039eab6ddc7421a773bf36b05e816dea02c4'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_BS_CD_native_20261114_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_launch_once_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', session='bcsp_scq_BS_CD_native_20261114_v1', forwards=420)))