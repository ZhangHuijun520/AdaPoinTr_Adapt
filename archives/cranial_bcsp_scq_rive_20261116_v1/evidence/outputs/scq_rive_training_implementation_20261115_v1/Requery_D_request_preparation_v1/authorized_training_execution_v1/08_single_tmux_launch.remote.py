import pathlib, json, hashlib, os, socket, shutil, subprocess, shlex
P = pathlib.Path
root = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1')
run = 'SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1'
p = root / (run + '_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'
q = json.loads(b)
I = q['identity']
L = q['launch_contract']
assert socket.gethostname() == I['hostname'] and os.getuid() == 1000
for path in (q['output'], q['launch_attempt']):
    p = P(path)
    assert not os.path.lexists(p) and (not any((x.is_symlink() for x in (p, *p.parents))))
for (name, h) in [('authorization_path', 'a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e'), ('runtime_path', '4fb7ad4408456198daabb01b81e6e8ff8cf877f67cb8f01437364b1a6b76bcb0'), ('launcher_path', 'dbb47722b5925a6dbccf3220c73bbed2581819f577b4b2f95f60ce5dbd5471dc')]:
    p = P(L[name])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (hashlib.sha256(p.read_bytes()).hexdigest() == h)
session = L['tmux_session']
assert subprocess.run(['tmux', 'has-session', '-t', '=' + session], capture_output=True).returncode == 1
args = ['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total,memory.used', '--format=csv,noheader,nounits']
gpu = [s.strip() for s in subprocess.check_output(args, text=True, timeout=10).strip().split(',')]
assert gpu[:4] == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4]) <= 256
assert shutil.disk_usage(I['project']).free >= 6442450944
with P(q['launch_attempt']).open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'), f)
    f.flush()
    os.fsync(f.fileno())
r = subprocess.run(['tmux', 'new-session', '-d', '-s', session, 'bash ' + shlex.quote(L['launcher_path'])], capture_output=True, text=True, timeout=10)
print(json.dumps(dict(status='SINGLE_TMUX_SUBMIT_RESULT', returncode=r.returncode, session=session, stdout=r.stdout, stderr=r.stderr, gpu=gpu)), flush=True)
assert r.returncode == 0
