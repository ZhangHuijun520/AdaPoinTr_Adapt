"""Bounded I_D prelaunch verification and separately authorized single dispatch."""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import zlib


REQUEST_SHA = "9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818"
REQUEST_NAME = "CISC_P2_I_D_training_execution_request_v1.json"
MAX_COMMAND_BYTES = 2048
CLIENT = [
    "wsl.exe", "-d", "Ubuntu-20.04", "--exec",
    "/home/zhj/.local/bin/hpc5000", "exec",
]

SOURCES = {
    "installed": r"""
import hashlib, json, os, shlex, shutil, socket, subprocess, time
from pathlib import Path

sha = '9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = project / 'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out = project / 'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
name = 'cisc_p2_i_d_20261125_v1'
req = root / 'CISC_P2_I_D_training_execution_request_v1.json'
launcher = root / 'launch_cisc_i_d_once_v1.sh'
auth, run = root / 'authorization_v1.json', root / 'runtime_v1.json'

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hashfile(path):
    need(path.resolve(strict=True) == path and path.is_file(), f'path: {path}')
    with path.open('rb') as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(path, size, digest):
    need(path.stat().st_size == size and hashfile(path) == digest, f'identity: {path}')

def record(item):
    verify(Path(item['path']), item['bytes'], item['sha256'])

def load(path):
    return json.loads(path.read_bytes())

def call(argv, timeout=8):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()
need((socket.gethostname(), os.getuid()) == ('shu-common-25721452-notebook-zrtpob-0', 1000), 'container identity')
need(root.resolve(strict=True) == root and out.parent.resolve(strict=True) == out.parent and out.parent.is_dir(), 'installation or output parents')
need(not os.path.lexists(out), 'output already exists')
files = {
 req.name: (18186, sha),
 'U_D_formal_post_training_freeze_receipt_v1.json': (7781,'f5f964d01ac997729e16a8f2cb5df822903b1c67af1929b4439bb3ceb700b137'),
 'cisc_train_i_d_v1.py': (16816,'ab46458bac6816b6a4e8ec5760af3835044050e0822d03c9d7ecc45a70d9e288'),
 launcher.name: (1390,'5df18880fa68b1eaa28878de849c7e4c22e0f286175dbe514a6d0bfeac79deff')}
need({p.name for p in root.iterdir()} == set(files), 'installed file set or attempt already materialized')
for key, values in files.items():
    verify(root / key, *values)
q = load(req)
need(q['project'] == str(project) and q['output'] == str(out) and q['run'] == dict(variant='I', fold='D', seed=2026112601)
     and q['counts']['updates'] == 3900 and q['policy']['single_attempt'] is True
     and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
     and q['controls'] == dict(request=str(req), authorization=str(auth), runtime=str(run)), 'request scope')
print('INSTALLED_OK 4')
""",
    "reused": r"""
import hashlib, json, os, shlex, shutil, socket, subprocess, time
from pathlib import Path

sha = '9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = project / 'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out = project / 'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
name = 'cisc_p2_i_d_20261125_v1'
req = root / 'CISC_P2_I_D_training_execution_request_v1.json'
launcher = root / 'launch_cisc_i_d_once_v1.sh'
auth, run = root / 'authorization_v1.json', root / 'runtime_v1.json'

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hashfile(path):
    need(path.resolve(strict=True) == path and path.is_file(), f'path: {path}')
    with path.open('rb') as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(path, size, digest):
    need(path.stat().st_size == size and hashfile(path) == digest, f'identity: {path}')

def record(item):
    verify(Path(item['path']), item['bytes'], item['sha256'])

def load(path):
    return json.loads(path.read_bytes())

def call(argv, timeout=8):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()
need((socket.gethostname(), os.getuid()) == ('shu-common-25721452-notebook-zrtpob-0', 1000), 'container identity')
need(root.resolve(strict=True) == root and out.parent.resolve(strict=True) == out.parent and out.parent.is_dir(), 'installation or output parents')
need(not os.path.lexists(out), 'output already exists')
need(hashfile(req) == sha, 'request SHA256')
q = load(req)
need(q['output'] == str(out) and q['project'] == str(project), 'request paths')
path_records = {}
def collect(obj):
    if isinstance(obj, dict):
        if {'path','bytes','sha256'} <= obj.keys() and isinstance(obj['path'], str) and obj['path'].startswith('/'):
            old = path_records.setdefault(obj['path'], obj)
            need((old['bytes'],old['sha256']) == (obj['bytes'],obj['sha256']), 'conflicting file bindings')
        for value in obj.values():
            collect(value)
    elif isinstance(obj, list):
        for value in obj:
            collect(value)
collect(q)
for entry in path_records.values():
    record(entry)
local_count = sum(Path(path).parent == root for path in path_records)
print('REUSED_OK', len(path_records) - local_count, local_count)
""",
    "training_inputs": r"""
import hashlib, json, os, shlex, shutil, socket, subprocess, time
from pathlib import Path

sha = '9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = project / 'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out = project / 'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
name = 'cisc_p2_i_d_20261125_v1'
req = root / 'CISC_P2_I_D_training_execution_request_v1.json'
launcher = root / 'launch_cisc_i_d_once_v1.sh'
auth, run = root / 'authorization_v1.json', root / 'runtime_v1.json'

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hashfile(path):
    need(path.resolve(strict=True) == path and path.is_file(), f'path: {path}')
    with path.open('rb') as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(path, size, digest):
    need(path.stat().st_size == size and hashfile(path) == digest, f'identity: {path}')

def record(item):
    verify(Path(item['path']), item['bytes'], item['sha256'])

def load(path):
    return json.loads(path.read_bytes())

def call(argv, timeout=8):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()
need((socket.gethostname(), os.getuid()) == ('shu-common-25721452-notebook-zrtpob-0', 1000), 'container identity')
need(root.resolve(strict=True) == root and out.parent.resolve(strict=True) == out.parent and out.parent.is_dir(), 'installation or output parents')
need(not os.path.lexists(out), 'output already exists')
need(hashfile(req) == sha, 'request SHA256')
q = load(req)
need(q['output'] == str(out) and q['project'] == str(project), 'request paths')
for key in ('common_contract','fold','point_manifest'):
    record(q[key])
rows = load(Path(q['common_contract']['path']))['label_contract']['rows']
need(set(rows) == set(load(Path(q['fold']['path']))['folds']['D']['train_case_ids']) and len(rows) == 315, 'Fold D case identity')
points = {entry['case_id']: entry for entry in map(json.loads, Path(q['point_manifest']['path']).read_bytes().splitlines()) if entry['case_id'] in rows}
need(set(points) == set(rows), 'manifest case set')
labels, data = Path(q['label_root']), Path(q['data_root'])
need(labels.resolve(strict=True) == labels and data.resolve(strict=True) == data
     and {p.name for p in labels.iterdir()} == {f'{case}_labels.npz' for case in rows}, 'training asset roots or label set')
for case, row in rows.items():
    point = data / points[case]['point_path']
    need(data in point.parents and points[case]['sha256'] == row['point_file_sha256'] == hashfile(point), f'training point: {case}')
    verify(labels / f'{case}_labels.npz', row['bytes'], row['sha256'])
print('TRAINING_INPUTS_OK 315 315')
""",
    "resources": r"""
import hashlib, json, os, shlex, shutil, socket, subprocess, time
from pathlib import Path

sha = '9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = project / 'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out = project / 'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
name = 'cisc_p2_i_d_20261125_v1'
req = root / 'CISC_P2_I_D_training_execution_request_v1.json'
launcher = root / 'launch_cisc_i_d_once_v1.sh'
auth, run = root / 'authorization_v1.json', root / 'runtime_v1.json'

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hashfile(path):
    need(path.resolve(strict=True) == path and path.is_file(), f'path: {path}')
    with path.open('rb') as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(path, size, digest):
    need(path.stat().st_size == size and hashfile(path) == digest, f'identity: {path}')

def record(item):
    verify(Path(item['path']), item['bytes'], item['sha256'])

def load(path):
    return json.loads(path.read_bytes())

def call(argv, timeout=8):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()
need((socket.gethostname(), os.getuid()) == ('shu-common-25721452-notebook-zrtpob-0', 1000), 'container identity')
need(root.resolve(strict=True) == root and out.parent.resolve(strict=True) == out.parent and out.parent.is_dir(), 'installation or output parents')
need(not os.path.lexists(out), 'output already exists')
need(hashfile(req) == sha, 'request SHA256')
q = load(req)
need(q['output'] == str(out) and q['project'] == str(project), 'request paths')
i, lim = q['identity'], q['resources']
py = Path(i['python_realpath'])
need(py.resolve(strict=True) == py and call([str(py), '-I', '-S', '-B', '--version']) == 'Python '+i['python_version'], 'Python identity')
smi = ['/usr/bin/nvidia-smi', '--id='+i['gpu_uuid']]
fmt = '--format=csv,noheader,nounits'
values = [x.strip() for x in call(smi+['--query-gpu=uuid,name,driver_version,memory.total,memory.used,memory.free',fmt]).split(',')]
need(len(values) == 6 and values[:4] == [i[k] for k in ('gpu_uuid','gpu_name','driver_version','total_MiB')], 'GPU identity')
used, free = map(int, values[4:])
disk = shutil.disk_usage(out.parent).free
print('RESOURCES', 'used_MiB', used, 'free_MiB', free, 'disk_bytes', disk, flush=True)
need(used <= lim['idle_used_MiB'] and free >= lim['minimum_start_free_MiB'] and
     not call(smi+['--query-compute-apps=pid',fmt]) and disk >= q['minimum_free_bytes_prelaunch'], 'startup capacity or GPU occupancy')
tmux = '/usr/bin/tmux'
need(Path(tmux).is_file(), 'tmux unavailable')
probe = subprocess.run([tmux,'has-session','-t','='+name], capture_output=True, text=True, timeout=8)
need(probe.returncode == 1 and not os.path.lexists(out), 'session or output already exists')
print('RESOURCES_OK')
""",
    "launch": r"""
import hashlib,json,os,pathlib,shlex,socket,subprocess
sha='9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr')
root=P/'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out=P/'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
req=root/'CISC_P2_I_D_training_execution_request_v1.json'
launcher=root/'launch_cisc_i_d_once_v1.sh'
name='cisc_p2_i_d_20261125_v1'
tmux='/usr/bin/tmux'
assert (socket.gethostname(),os.getuid())==('shu-common-25721452-notebook-zrtpob-0',1000)
assert root.resolve(strict=True)==root and out.parent.resolve(strict=True)==out.parent
assert out.parent.is_dir() and not os.path.lexists(out)
assert req.resolve(strict=True)==req and hashlib.sha256(req.read_bytes()).hexdigest()==sha
q=json.loads(req.read_bytes())
assert launcher.resolve(strict=True)==launcher
assert hashlib.sha256(launcher.read_bytes()).hexdigest()==q['launcher']['sha256']
assert subprocess.run([tmux,'has-session','-t','='+name],capture_output=True,timeout=5).returncode==1
assert not any(os.path.lexists(q['controls'][k]) for k in ('authorization','runtime'))
os.umask(0o077)
def write(key,obj):
    body=(json.dumps(obj,sort_keys=True)+'\n').encode('ascii')
    with open(q['controls'][key],'xb') as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())
    return hashlib.sha256(body).hexdigest()
a=write('authorization',dict(request_sha256=sha,explicit_user_authorization=True,authorization_text='Explicitly authorized I_D training request '+sha))
r=write('runtime',dict(request_sha256=sha,authorization_sha256=a))
pane=subprocess.check_output([tmux,'new-session','-d','-P','-F','#{pane_id}','-s',name,'-c',str(P),'/bin/sh'],text=True,timeout=5).strip()
subprocess.run([tmux,'set-option','-w','-t',pane,'remain-on-exit','on'],check=True,timeout=5)
command=' '.join(map(shlex.quote,['/bin/bash',str(launcher),sha,a,r]))+' && '+tmux+' kill-session -t ='+name
subprocess.run([tmux,'respawn-pane','-k','-t',pane,command],check=True,timeout=5)
print('SINGLE_LAUNCH_DISPATCHED',name,flush=True)
""",
    "confirm": r"""
import hashlib, json, os, shlex, shutil, socket, subprocess, time
from pathlib import Path

sha = '9744b973329433c5b84b3974139d11c8ec418a5ea6d28e100439db0a99381818'
project = Path('/home/jovyan/adapointr_work/PoinTr')
root = project / 'third_party/bcsp_cisc_p2_i_d_20261125_v1'
out = project / 'logs/cranial_bcsp_fullmamba/CISC_P2_I_D_seed2026112601_zrtpob_v1'
name = 'cisc_p2_i_d_20261125_v1'
req = root / 'CISC_P2_I_D_training_execution_request_v1.json'
launcher = root / 'launch_cisc_i_d_once_v1.sh'
auth, run = root / 'authorization_v1.json', root / 'runtime_v1.json'

def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)

def hashfile(path):
    need(path.resolve(strict=True) == path and path.is_file(), f'path: {path}')
    with path.open('rb') as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()

def verify(path, size, digest):
    need(path.stat().st_size == size and hashfile(path) == digest, f'identity: {path}')

def record(item):
    verify(Path(item['path']), item['bytes'], item['sha256'])

def load(path):
    return json.loads(path.read_bytes())

def call(argv, timeout=8):
    return subprocess.check_output(argv, text=True, timeout=timeout).strip()
need((socket.gethostname(), os.getuid()) == ('shu-common-25721452-notebook-zrtpob-0', 1000), 'container identity')
tmux = '/usr/bin/tmux'
for _ in range(34):
    exit_file = out / 'exit_code.txt'
    pid_file = out / 'launcher.pid'
    if exit_file.is_file():
        raise RuntimeError('worker exit code: '+exit_file.read_text().strip())
    if pid_file.is_file():
        pid = pid_file.read_text().strip()
        need(pid.isdigit() and Path('/proc',pid).is_dir(), 'launcher PID not live')
        print('TRAINING_LAUNCHER_ACTIVE',pid)
        break
    pane = call([tmux,'display-message','-p','-t','='+name,'#{pane_dead}'])
    if pane == '1':
        print(call([tmux,'capture-pane','-p','-t','='+name,'-S','-12']),flush=True)
        raise RuntimeError('launcher exited before training')
    time.sleep(1)
else:
    raise RuntimeError('launch not yet confirmed; inspect only')
""",
}

STAGES = (
    ("installed", 15, "INSTALLED_OK 4"),
    ("reused", 45, "REUSED_OK 49 3"),
    ("training_inputs", 55, "TRAINING_INPUTS_OK 315 315"),
    ("resources", 25, "RESOURCES_OK"),
    ("launch", 35, "SINGLE_LAUNCH_DISPATCHED cisc_p2_i_d_20261125_v1"),
    ("confirm", 40, "TRAINING_LAUNCHER_ACTIVE "),
)


def render(stage, seconds):
    source = SOURCES[stage].lstrip("\n").encode("ascii")
    compile(source, stage, "exec")
    packed = base64.b64encode(zlib.compress(source, level=9)).decode("ascii")
    if zlib.decompress(base64.b64decode(packed, validate=True)) != source:
        raise RuntimeError(f"{stage} byte round-trip")
    command = (
        f"/usr/bin/timeout --kill-after=3s {seconds}s /usr/bin/python3 -IBc "
        f"'import base64,zlib;exec(zlib.decompress(base64.b64decode(\"{packed}\")))'"
    )
    size = len(command.encode("ascii"))
    if size > MAX_COMMAND_BYTES:
        raise RuntimeError(f"{stage} command is {size} bytes")
    return command


def emit(**record):
    print(json.dumps(record, ensure_ascii=True), flush=True)


def execute(stage, command, seconds, marker):
    start = time.monotonic()
    emit(stage=stage, status="SENDING", bytes=len(command.encode("ascii")))
    try:
        result = subprocess.run(
            [*CLIENT, "--timeout", str(seconds + 4), "--", command],
            capture_output=True, timeout=seconds + 9, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        emit(stage=stage, status="LOCAL_TIMEOUT", seconds=round(time.monotonic() - start, 2),
             stdout=(exc.stdout or b"").decode("utf-8", "replace"))
        raise RuntimeError(f"{stage} timed out; stop and inspect") from None
    output = result.stdout.decode("utf-8", "replace").splitlines()
    actual = [line for line in output if line.startswith(marker)] if stage == "confirm" else [
        line for line in output if line == marker
    ]
    emit(stage=stage, returncode=result.returncode, seconds=round(time.monotonic() - start, 2),
         stdout=output, stderr_bytes=len(result.stderr))
    if result.returncode or len(actual) != 1:
        raise RuntimeError(f"{stage} failed or lacks a unique receipt; stop and inspect")


def main():
    parser = argparse.ArgumentParser()
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--check-only", action="store_true")
    options.add_argument("--execute-request-sha256")
    args = parser.parse_args()
    req = Path(__file__).with_name(REQUEST_NAME)
    if hashlib.sha256(req.read_bytes()).hexdigest() != REQUEST_SHA:
        raise RuntimeError("local request SHA256 mismatch")
    if args.execute_request_sha256 is not None and args.execute_request_sha256 != REQUEST_SHA:
        raise RuntimeError("execute-request SHA256 mismatch")
    commands = [(stage, render(stage, seconds), seconds, marker) for stage, seconds, marker in STAGES]
    if args.execute_request_sha256 is None and not args.check_only:
        for stage, command, _, _ in commands:
            emit(stage=stage, status="STATIC_OK", bytes=len(command.encode("ascii")))
        return
    selected = commands if args.execute_request_sha256 is not None else commands[:4]
    for stage, command, seconds, marker in selected:
        execute(stage, command, seconds, marker)
    if args.check_only:
        emit(status="READ_ONLY_CHECKS_PASSED")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as error:
        emit(status="STOP_NO_RETRY", error=str(error))
        sys.exit(1)
