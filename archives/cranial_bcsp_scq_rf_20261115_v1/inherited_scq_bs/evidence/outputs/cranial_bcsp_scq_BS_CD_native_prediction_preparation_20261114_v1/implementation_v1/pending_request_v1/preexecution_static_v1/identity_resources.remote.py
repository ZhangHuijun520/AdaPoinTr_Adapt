from pathlib import Path
import socket, os, subprocess, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
p = Path('/home/jovyan/adapointr_work/PoinTr')
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v1')
assert p.is_dir() and p.resolve() == p and root.parent.is_dir() and out.parent.is_dir()
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents)))), str(x)
assert shutil.disk_usage(p).free >= 4294967296
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_BS_CD_native_20261114_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256, a
assert str(Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').resolve()) == '/opt/conda/envs/adapointr-mamba/bin/python3.10'
v = subprocess.check_output(['/opt/conda/envs/adapointr-mamba/bin/python3.10', '-I', '-S', '-B', '-c', 'import sys;print(sys.version.split()[0])'], text=True, timeout=10).strip()
assert v == '3.10.20'
print(json.dumps(dict(status='FRESH_IDENTITY_RESOURCES_NEW_ROOT_PASS', hostname=socket.gethostname(), GPU=a, free_disk=shutil.disk_usage(p).free, python_version=v)))