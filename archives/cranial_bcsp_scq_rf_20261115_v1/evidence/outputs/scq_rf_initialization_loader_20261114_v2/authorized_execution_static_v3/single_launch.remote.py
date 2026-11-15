from pathlib import Path
import socket, os, subprocess, shutil, json, hashlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v3')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/attempt_claim_v3.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_cuda_20261114_v3'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (path, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/authorization_v3.json', 'f720da27fec89a92ca737b98d4105bfbada5465fc3fc65d8c32e980fb7bf90c5'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/runtime_v3.json', '58e8e47b15ceee37cb23c019bab371a5e40879b6933ce799857c4affb0e26d03'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/launch_once_v3.sh', '78867d9a73448c0692e2535cf4ee685606b8b8246c75c97752528f72ba8cca29')]:
    p = Path(path)
    assert not any((x.is_symlink() for x in (p, *p.parents))) and hashlib.sha256(p.read_bytes()).hexdigest() == h
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'), f)
r = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_cuda_20261114_v3', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/control/launch_once_v3.sh'])
assert r.returncode == 0
print(json.dumps(dict(status='SINGLE_RF_CUDA_TMUX_SUBMITTED', session='bcsp_scq_rf_cuda_20261114_v3', GPU=a)))