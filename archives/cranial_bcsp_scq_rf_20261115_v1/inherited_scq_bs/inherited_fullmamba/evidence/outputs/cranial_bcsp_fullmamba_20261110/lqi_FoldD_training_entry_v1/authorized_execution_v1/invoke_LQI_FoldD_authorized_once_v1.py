"""Original-byte operation transport. One attempt, raw stdout/stderr, no retry."""
import ast
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time

A = Path(__file__).resolve().parent
B = A.parent
QH = '41e53b39f099e502e3a1abebab952b9ea98acd58d1616e128312a0685a6bb517'
SOURCE = A/'execute_LQI_FoldD_authorized_once_v1.py'
TARGET = '/home/jovyan/adapointr_work/PoinTr/third_party/lqi_FoldD_training_authorized_once_20261111_v1.py'
BASE = ['wsl.exe', '-d', 'Ubuntu-20.04', '--exec']
CLIENT = '/home/zhj/.local/bin/hpc5000'
EVENTS = []


def emit(name, value):
    with (A/name).open('x', encoding='ascii') as f:
        json.dump(value, f, indent=2, allow_nan=False)


def invoke(label, args, timeout):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    for key, blob in [('stdout', result.stdout), ('stderr', result.stderr)]:
        with (A/(label+'_'+key+'.bin')).open('xb') as f:
            f.write(blob)
    event = dict(stage=label, returncode=result.returncode, stdout_bytes=len(result.stdout),
                 stderr_bytes=len(result.stderr), stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                 stderr_sha256=hashlib.sha256(result.stderr).hexdigest())
    EVENTS.append(event); print(json.dumps(event), flush=True)
    if result.returncode != 0:
        raise RuntimeError('stage failed, stop without retry: '+label)
    return result.stdout


def main():
    start = time.monotonic()
    try:
        blob = SOURCE.read_bytes(); helper_sha = hashlib.sha256(blob).hexdigest()
        ast.parse(blob.decode('utf-8'))
        assert hashlib.sha256((B/'LQI_FoldD_training_execution_request_v1.json').read_bytes()).hexdigest() == QH
        assert not (A/'local_single_execution_claim_v1.json').exists()
        emit('local_single_execution_claim_v1.json', dict(status='CLAIMED_BEFORE_AUTHORIZED_OPERATION_TRANSPORT',
             request_sha256=QH, explicit_user_authorization='已上传，单独授权此request完整SHA256，才能不覆盖安装并启动唯一一次Fold D训练',
             operation_helper_sha256=helper_sha, no_retry=True))
        source_wsl = invoke('resolve_operation_source', BASE+['wslpath', '-a', str(SOURCE)], 15).decode('utf-8').strip()
        assert source_wsl.startswith('/mnt/e/') and '\n' not in source_wsl
        command = 'test ! -e '+shlex.quote(TARGET)+' && test ! -L '+shlex.quote(TARGET)+' && test -d /home/jovyan/adapointr_work/PoinTr/third_party'
        invoke('staging_control_absent', BASE+[CLIENT, 'exec', '--timeout', '15', '--', command], 25)
        invoke('put_exact_operation_control', BASE+[CLIENT, 'put', source_wsl, TARGET], 45)
        code = 'import pathlib,hashlib; p=pathlib.Path('+repr(TARGET)+'); assert not any(x.is_symlink() for x in (p,*p.parents)); b=p.read_bytes(); assert hashlib.sha256(b).hexdigest()=='+repr(helper_sha)+'; exec(compile(b,str(p),"exec"))'
        command = shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10', '-I', '-S', '-B', '-c', code])
        assert len(command.encode()) <= 2048
        stdout = invoke('verify_install_materialize_single_launch', BASE+[CLIENT, 'exec', '--timeout', '150', '--', command], 165)
        print(json.dumps(dict(operation_stdout=stdout.decode('utf-8', errors='replace')[-16000:]), ensure_ascii=True), flush=True)
        result = dict(status='AUTHORIZED_OPERATION_RETURNED_INSPECT_STARTUP', request_sha256=QH,
                      events=EVENTS, seconds=time.monotonic()-start, automatic_retry=False)
    except BaseException as exc:
        result = dict(status='FAILED_STOP_NO_RETRY', error=repr(exc), request_sha256=QH,
                      events=EVENTS, seconds=time.monotonic()-start)
    emit('local_authorized_operation_result_v1.json', result)
    print(json.dumps(result, ensure_ascii=True), flush=True)
    return 1 if result['status'] == 'FAILED_STOP_NO_RETRY' else 0


if __name__ == '__main__':
    sys.exit(main())
