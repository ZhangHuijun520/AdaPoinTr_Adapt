"""Execute the explicitly authorized, hash-frozen local RF CPU batch once."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'
SCOPE_SHA = 'd512ffbb57622357a14e32c96befbe5b17337d01ca7d3ffa8ecb538b0d49c5f2'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def emit(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)


scope_path = O / 'CPU_validation_scope_v2.json'
assert digest(scope_path) == SCOPE_SHA
scope = json.loads(scope_path.read_bytes())
assert scope['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and scope['execution_authorized'] is False
for record in (scope['test'], scope['static_review']):
    path = Path(record['path'])
    assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256']
static = json.loads(Path(scope['static_review']['path']).read_bytes())
for record in static['frozen_files'] + static['preserved_artifacts']:
    path = Path(record['path'])
    assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256']
assert not Path(scope['output']).exists()
receipt_dir = O / 'CPU_validation_authorized_execution_v2'
receipt_dir.mkdir()
emit(receipt_dir / 'authorization_v2.json', dict(scope_sha256=SCOPE_SHA,
     explicit_user_authorization=True, user_text='单独授权，执行唯一一次新版人工CPU验证。',
     production_or_initialization_modification=False, CUDA=False, training=False))
emit(receipt_dir / 'single_attempt_claim_v2.json', dict(status='CLAIMED_BEFORE_PROCESS_START', scope_sha256=SCOPE_SHA))
command = [scope['python'], *scope['python_flags'], scope['test']['path']]
start = time.monotonic()
env = os.environ.copy()
env['CUDA_VISIBLE_DEVICES'] = ''
try:
    with (receipt_dir / 'stdout_v2.bin').open('xb') as stdout, (receipt_dir / 'stderr_v2.bin').open('xb') as stderr:
        result = subprocess.run(command, cwd=str(R), env=env, stdout=stdout, stderr=stderr, timeout=600, check=False)
    emit(receipt_dir / 'process_exit_v2.json', dict(returncode=result.returncode, seconds=time.monotonic()-start,
         scope_sha256=SCOPE_SHA, no_retry=True))
    print(json.dumps(dict(status='CPU_PROCESS_FINISHED', returncode=result.returncode, seconds=time.monotonic()-start)))
except BaseException as exc:
    emit(receipt_dir / 'launch_failure_v2.json', dict(status='FAILED_STOP_NO_RETRY', error=repr(exc), seconds=time.monotonic()-start))
    raise
