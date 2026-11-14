from pathlib import Path
import os, socket, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/launch_attempt_v1.json')
assert not out.exists() and (not claim.exists()) and (not any((x.is_symlink() for x in (claim, *claim.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_cuda_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/authorization_v1.json', '1dc78f1c2c9662bae6a2798e72b22ceaa70fe4e38d39fb3336728d84da11306e'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/runtime_v1.json', 'e405a679c6b18425c4980e4fefc4e23a628c7cfe862a834f7293d7efeacba8b9'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/launch_once_v1.sh', 'e2cb9f277217672169de8eea5bd4571dc976c0f96b43f27a320763a19f33153f')]:
    path = Path(p)
    assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_cuda_20261113_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/launch_once_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', GPU=a, session='bcsp_scq_cuda_20261113_v1')))