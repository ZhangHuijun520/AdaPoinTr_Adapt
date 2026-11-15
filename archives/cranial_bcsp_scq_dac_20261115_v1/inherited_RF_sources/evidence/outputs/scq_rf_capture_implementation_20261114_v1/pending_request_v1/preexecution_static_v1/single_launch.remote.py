from pathlib import Path
import socket, os, subprocess, hashlib, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_memory_20261114_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/authorization_v1.json', '235c1a571a16d8d1fe756397a5b4f901b4e57b5ff45e24be72d20fee1ef556c9'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/runtime_v1.json', '4457700eecf38cde42eb90034f918209c0baf75152332d01278c481fd48f54f0'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/launch_once_v1.sh', 'f323bb51b05695d8bf17e6e25f4743e61a450536ba90c215d322b59c677e9d6c')]:
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h and (not Path(p).is_symlink())
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_memory_20261114_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/launch_once_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', session='bcsp_scq_rf_memory_20261114_v1', forwards=10)))