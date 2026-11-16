import pathlib, hashlib, json, os, socket, shutil, subprocess, sys
P = pathlib.Path
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Static_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2'
q = json.loads(b)
I = q['identity']
assert socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] == 1000
assert str(P(sys.executable).resolve()) == I['python_realpath'] and sys.version.split()[0] == I['python_version']
os.chdir(I['project'])
assert str(P.cwd().resolve()) == I['project']
paths = [q['output'], q['launch_attempt'], *list(q['launch_contract'].values())[:4]]
paths.append(str(pathlib.PurePosixPath(q['launch_attempt']).parent))
for s in paths:
    x = P(s)
    if s == str(p):
        continue
    assert not os.path.lexists(x) and (not any((z.is_symlink() for z in (x, *x.parents)))), s
assert P(q['output']).parent.is_dir()
free = shutil.disk_usage(I['project']).free
assert free >= 6442450944
session = q['launch_contract']['tmux_session']
assert subprocess.run(['tmux', 'has-session', '-t', '=' + session], capture_output=True).returncode == 1
args = ['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits']
gpu = [x.strip() for x in subprocess.check_output(args, text=True, timeout=10).strip().split(',')]
assert gpu[:4] == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4]) <= 256
print(json.dumps(dict(status='FRESH_RESOURCE_AND_ABSENCE_PASS', hostname=socket.gethostname(), uid=os.getuid(), gpu=gpu, free_bytes=free, session_absent=True, controls_absent=True, output_absent=True)))
