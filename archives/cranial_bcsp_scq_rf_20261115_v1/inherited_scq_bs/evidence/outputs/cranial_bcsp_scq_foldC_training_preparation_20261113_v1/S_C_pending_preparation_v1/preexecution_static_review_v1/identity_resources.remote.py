from pathlib import Path
import os, socket, subprocess, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1')
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
for p in [out, Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1')]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
assert root.parent.is_dir() and out.parent.is_dir()
assert shutil.disk_usage(root.parent).free >= 4294967296
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_S_foldC_20261113_v1'], capture_output=True).returncode == 1
g = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
a = [x.strip() for x in g.split(',')]
assert a[:4] == ['GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714', 'NVIDIA GeForce RTX 4090 D', '570.190', '24564'] and int(a[4]) <= 256, a
print(json.dumps(dict(status='FRESH_IDENTITY_RESOURCES_TARGETS_PASS', hostname=socket.gethostname(), GPU=a, free_disk_bytes=shutil.disk_usage(root.parent).free)))