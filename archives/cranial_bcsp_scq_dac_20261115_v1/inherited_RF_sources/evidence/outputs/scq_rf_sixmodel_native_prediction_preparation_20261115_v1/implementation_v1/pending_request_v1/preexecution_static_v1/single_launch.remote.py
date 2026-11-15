from pathlib import Path
import socket, os, subprocess, hashlib, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v1')
claim = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/attempt_claim_v1.json')
for p in [out, claim]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_six_native_20261115_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-383d118a-368c-94e3-166a-cad3efab8fd7', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256 and (shutil.disk_usage(out.parent).free >= 4294967296)
for (p, h) in [('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json', '56ef2d970f5b384018b48df1e7bb813d91ef4b46f191ef14d1cacbb8764cda49'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json', '7a25572a9068db05f2db1427182f58e2bd4d62ea7624f0b862d0653c3343e416'), ('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_launch_once_v1.sh', '63c220e6f99e5d49039a455c065fc362cfae748e455cce186b302398706c8292')]:
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest() == h and (not Path(p).is_symlink())
with claim.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_rf_six_native_20261115_v1', 'bash ' + '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_launch_once_v1.sh'])
assert x.returncode == 0
print(json.dumps(dict(status='SINGLE_TMUX_SUBMITTED', session='bcsp_scq_rf_six_native_20261115_v1', forwards=630)))