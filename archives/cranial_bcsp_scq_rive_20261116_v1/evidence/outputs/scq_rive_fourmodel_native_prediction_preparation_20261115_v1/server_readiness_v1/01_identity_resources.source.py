import pathlib, json, hashlib, os, socket
P = pathlib.Path
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'
q = json.loads(b)
I = q['identity']
assert socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] == 1000
import shutil, subprocess, sys
assert str(P(sys.executable).resolve()) == I['python_realpath'] and sys.version.split()[0] == I['python_version']
os.chdir(I['project'])
assert str(P.cwd().resolve()) == I['project']
root = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
out = P('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
for p in (root, out):
    assert p.parent.is_dir() and (not os.path.lexists(p)) and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
g = [x.strip() for x in subprocess.check_output(['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert g[:4] == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])] and int(g[4]) <= 256
free = shutil.disk_usage(I['project']).free
assert free >= 5368709120
assert subprocess.run(['tmux', 'has-session', '-t', '=bcsp_scq_rive_four_native_20261115_v1'], capture_output=True).returncode == 1
print(json.dumps(dict(status='IDENTITY_RESOURCE_NEW_ROOTS_PASS', hostname=socket.gethostname(), uid=os.getuid(), gpu=g, free_bytes=free, required_free_bytes=5368709120, new_install_root_absent=True, new_output_absent=True, new_session_absent=True, server_writes=0)))
