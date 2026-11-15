from pathlib import Path
import os, socket, subprocess, shutil, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000, dict(expected='shu-common-25721452-notebook-zbpgzu-0', observed=socket.gethostname(), uid=os.getuid())
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3')
assert project.is_dir() and project.resolve() == project
os.chdir(project)
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
assert root.parent.is_dir() and out.parent.is_dir() and (shutil.disk_usage(project).free >= 4294967296)
assert subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_Sref_C_train_20261114_v3'], capture_output=True).returncode == 1
a = [x.strip() for x in subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert a[:4] == ['GPU-dabcc897-ac69-efac-4438-a6186dea9aaa', 'NVIDIA GeForce RTX 4090 D', '575.51.03', '24564'] and int(a[4]) <= 256, a
assert Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').resolve() == Path('/opt/conda/envs/adapointr-mamba/bin/python3.10')
v = subprocess.check_output(['/opt/conda/envs/adapointr-mamba/bin/python3.10', '-I', '-S', '-B', '-c', 'import sys;print(sys.version.split()[0])'], text=True, timeout=10).strip()
assert v == '3.10.20'
git = subprocess.run(['git', 'status', '--short', '--branch'], capture_output=True, text=True, timeout=10)
print(json.dumps(dict(status='FRESH_IDENTITY_RESOURCES_ABSENT_ROOT_PASS', hostname=socket.gethostname(), uid=os.getuid(), project=os.getcwd(), GPU=a, free_disk=shutil.disk_usage(project).free, python_version=v, git_status=git.stdout[:1000], git_returncode=git.returncode)))