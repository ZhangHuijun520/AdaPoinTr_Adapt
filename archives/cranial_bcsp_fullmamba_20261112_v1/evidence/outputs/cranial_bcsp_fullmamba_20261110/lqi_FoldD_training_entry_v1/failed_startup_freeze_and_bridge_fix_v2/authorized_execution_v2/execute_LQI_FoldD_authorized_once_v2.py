"""Frozen-request deployment/materialization and ONE tmux claim. No retry."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import subprocess
import sys
import tarfile
import time

QH = '317870937023da177930437f39b3179956e72e3773f53f4010eb86f25ed21da9'
AH = 'f7ad44831a38030ef5f3bd2ffa3e0e8e4757e45d8d7646f4e828aa2b5f62c922'
ARCHIVE = Path('/home/jovyan/bcsp_lqi_FoldD_training_pending_20261111_v2.tar.gz')
INSTALL = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2')
PROJECT = Path('/home/jovyan/adapointr_work/PoinTr')
START = time.monotonic()
READ = 0
PHASE = 'start'
ROWS = []
FROZEN_TARGETS = [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/bcsp_lqi_foldD_training_entry_v2.py', 'bytes': 24347, 'sha256': 'da0ee57a201decd21413351d6578607d46552bd4247a16ef41a2d05a9ce738ac'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/training_entry_P3_v2.json', 'bytes': 4318, 'sha256': 'f2b1470ce29682621bbc18e835543896a5d86d97fb1734d60975f46af5a44c87'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/FoldD_readiness_receipt_v2.json', 'bytes': 70719, 'sha256': '303dbf6d950679d6a4008fc46f479dabafc1d0391229c8cbd3b7414c1e3e039f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/LQI_FoldD_training_execution_request_v2.json', 'bytes': 15398, 'sha256': '317870937023da177930437f39b3179956e72e3773f53f4010eb86f25ed21da9'}]


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def clean(path):
    p = Path(path)
    need(p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents)), 'linked/nonabsolute: '+str(p))
    need(p == PROJECT or PROJECT in p.parents or p == ARCHIVE or
         p.parent == ARCHIVE.parent or str(p).startswith('/opt/conda/envs/adapointr-mamba/')
         or p == Path('/usr/share/zoneinfo/Etc/UTC'), 'unbound operation path: '+str(p))
    return p


def exact(r):
    global READ
    p = clean(r['path']); before = p.stat()
    need(p.is_file() and before.st_size == r['bytes'], 'file type/size: '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            READ += len(b)
            need(READ <= 2*1024**3 and time.monotonic()-START <= 120, 'bounded verification budget')
            h.update(b)
    after = p.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'read drift: '+str(p))
    need(h.hexdigest() == r['sha256'], 'hash mismatch: '+str(p))
    ROWS.append(r); return p


def sha(path):
    return hashlib.sha256(clean(path).read_bytes()).hexdigest()


def emit(path, obj):
    with clean(path).open('x', encoding='ascii') as f:
        json.dump(obj, f, indent=2, allow_nan=False); f.write('\n'); f.flush(); os.fsync(f.fileno())


def stage(name):
    global PHASE
    PHASE = name
    print(json.dumps(dict(phase=name, seconds=time.monotonic()-START, hashed_bytes=READ)), flush=True)


def smi(identity):
    raw = subprocess.check_output(['/usr/bin/nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used',
                                   '--format=csv,noheader,nounits'], timeout=10, text=True)
    rows = raw.strip().splitlines(); need(len(rows) == 1, 'one physical GPU')
    values = [x.strip() for x in rows[0].split(',')]
    need(values[:4] == [identity['gpu_uuid'], identity['gpu_name'], identity['driver_version'],
                        str(identity['nvidia_smi_memory_total_MiB'])] and int(values[4]) <= 256, 'GPU identity/idle')
    return values


def session_absent(name):
    r = subprocess.run(['tmux', 'has-session', '-t', name], capture_output=True, timeout=5)
    need(r.returncode == 1, 'session present/unknown tmux state')


def main():
    stage('identity_archive_and_frozen_request')
    need(socket.gethostname() == 'shu-common-25721452-notebook-zv9bqd-0' and os.getuid() == 1000, 'identity')
    exact(dict(path=str(ARCHIVE), bytes=20065, sha256=AH))
    for record in [{'path': '/home/jovyan/bcsp_lqi_FoldD_training_pending_20261111_v2.tar.gz.sha256', 'bytes': 118, 'sha256': 'f36f2fe4e59c467ec009087e8544c1443501ce378351c9941918ae1e7385d28f'}, {'path': '/home/jovyan/bcsp_lqi_FoldD_training_pending_20261111_v2.tar.gz.bytes', 'bytes': 7, 'sha256': 'f2119bc40be3737d5741fc1240375006f65a04da5f1ed88c39d4cd9b2706d999'}, {'path': '/home/jovyan/bcsp_lqi_FoldD_training_pending_20261111_v2.tar.gz.contents.sha256', 'bytes': 407, 'sha256': '2da84e3c43b91041ca67e31f3542696b5e843c05c8d50a4594447d205fc5e06d'}]:
        exact(record)
    need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0] == AH and
         int(Path(str(ARCHIVE)+'.bytes').read_text()) == 20065, 'archive sidecars')
    payload = {}
    with tarfile.open(ARCHIVE, 'r:gz') as tar:
        members = tar.getmembers(); need(len(members) == 4, 'eleven members')
        for member in members:
            need(member.isfile() and member.name == Path(member.name).name and member.name not in payload
                 and member.size <= 2*1024**2, 'archive member boundary')
            payload[member.name] = tar.extractfile(member).read()
    qb = payload['LQI_FoldD_training_execution_request_v2.json']
    need(hashlib.sha256(qb).hexdigest() == QH, 'explicitly authorized request hash')
    q = json.loads(qb); I = q['identity']; L = q['launch_contract']; out = clean(q['output'])
    need(Path(q['implementation']['entry']['path']).parent == INSTALL and I['project'] == str(PROJECT), 'frozen roots')
    need(str(Path(sys.executable).resolve()) == I['python_realpath'] and sys.version.split()[0] == I['python_version'], 'Python identity')
    expected = {Path(r['path']).name: r for r in FROZEN_TARGETS}
    expected['LQI_FoldD_training_execution_request_v2.json'] = dict(path=L['request_path'], bytes=len(qb), sha256=QH)
    need(set(payload) == set(expected) and len(expected) == 4, 'exact installation set')
    for name, r in expected.items():
        need(clean(r['path']).parent == INSTALL and len(payload[name]) == r['bytes']
             and hashlib.sha256(payload[name]).hexdigest() == r['sha256'], 'member binding: '+name)
    listing = ''.join(hashlib.sha256(blob).hexdigest()+'  '+name+'\n' for name, blob in payload.items())
    need(Path(str(ARCHIVE)+'.contents.sha256').read_text() == listing, 'exact content sidecar')
    need(not clean(INSTALL).exists() and not out.exists() and INSTALL.parent.is_dir() and PROJECT.is_dir(), 'fresh safe parents')
    session_absent(L['tmux_session']); smi(I)
    need(shutil.disk_usage(PROJECT).free >= json.loads(exact(q['static_config']).read_bytes())['resources']['minimum_free_disk_bytes'], 'disk budget')
    stage('reused_source_provider_and_extension_hashes')
    for r in [q['preflight_scope'],q['static_config'],q['order_plan'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*[v for k,v in q['implementation'].items() if k != 'entry'],*q['dependencies']]:
        exact(r)
    for r in list(q['admission'].values())+list(q['FoldC_pairing'].values())+[q['pair_contract'],q['FoldD_reference']]:
        need(not str(r['path']).startswith(str(INSTALL)+'/'),'reused evidence outside new install');exact(r)
    bindings = json.loads(Path(q['preflight_scope']['path']).read_bytes())['bindings']
    modelroot = clean(q['model_root'])
    for r in bindings['candidate']:
        exact(dict(path=str(modelroot/r['relative_target']), bytes=r['bytes'], sha256=r['sha256']))
    for r in bindings['isolated_model_project_sources']:
        exact(dict(path=str(modelroot/r['relative_path']), bytes=r['bytes'], sha256=r['sha256']))
    for r in bindings['provider']+bindings['environment_metadata']:
        exact(r)
    need(sha(modelroot/'base_model.yaml') == bindings['base_config']['sha256'], 'base config')
    utc = dict(link='/usr/share/zoneinfo/UTC',link_text='Etc/UTC',target='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a'); link = Path(utc['link'])
    need(link.is_symlink() and os.readlink(link) == utc['link_text'] and
         str(link.resolve(strict=True)) == utc['target'], 'exact UTC link')
    exact(dict(path=utc['target'], bytes=utc['bytes'], sha256=utc['sha256']))
    stage('fixed315_training_payload_hashes_before_install')
    import importlib.util
    contract_path=Path(q['implementation']['contract']['path'])
    spec=importlib.util.spec_from_file_location('f0_install_metadata_review',contract_path)
    metadata=importlib.util.module_from_spec(spec);spec.loader.exec_module(metadata)
    selected,fold=metadata.verify_qualified_receipt(json.loads(Path(q['QC']['qualified_receipt']['path']).read_bytes()),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'D',8192)
    metadata.validate_order(json.loads(Path(q['order_plan']['path']).read_bytes()),fold['train_case_ids'])
    for row in selected:
        rel=Path(row['point_path']);need(not rel.is_absolute() and '..' not in rel.parts,'point path')
        p=clean(Path(q['data_root'])/rel)
        exact(dict(path=str(p),bytes=p.stat().st_size,sha256=row['sha256']))
    need(len(selected)==315 and len(fold['train_sources'])==63,'train count/source')
    stage('all_readiness_pass_before_exclusive_install')
    need(not clean(INSTALL).exists() and not out.exists(), 'target drift')
    for r in expected.values():
        need(not clean(r['path']).exists(), 'target already exists')
    smi(I); INSTALL.mkdir()
    for name, blob in payload.items():
        with clean(INSTALL/name).open('xb') as f:
            f.write(blob); f.flush(); os.fsync(f.fileno())
        exact(expected[name])
    control = INSTALL/'control'; control.mkdir()
    emit(control/'readiness_and_installation_receipt_v1.json', dict(status='FOUR_EXCLUSIVE_INSTALL_HASHES_PASS',
         request_sha256=QH, archive_sha256=AH, targets=[expected[n] for n in payload],
         read_manifest=ROWS, verification_seconds=time.monotonic()-START,
         training_payload_files_hashed=315, payload_arrays_read=0, checkpoint_reads=0, overwritten_files=0))
    stage('materialize_one_way_authorization_runtime_launcher')
    auth = dict(schema='bcsp-lqi-training-authorization-v1', request_sha256=QH, explicit_user_authorization=True,
                user_authorization_text='2026-11-11: In reply to the complete request SHA256 '+QH+
                ', user explicitly answered: 已上传，单独授权此request完整SHA256，才能不覆盖安装并启动唯一一次Fold D训练. Exactly Fold C 8k/8k 3900 steps. Failure stops, no retry/resume/BNCal/evaluation.')
    emit(L['authorization_path'], auth); auth_sha = sha(L['authorization_path'])
    runtime = dict(schema='bcsp-lqi-training-runtime-v1', request_sha256=QH, authorization_sha256=auth_sha)
    emit(L['runtime_path'], runtime); runtime_sha = sha(L['runtime_path'])
    # The exact entry is stdlib-only on import. Only call its authorization and renderer here.
    namespace = dict(__name__='f0_authorized_launcher_render', __file__=q['implementation']['entry']['path'])
    exec(compile(exact(q['implementation']['entry']).read_bytes(), q['implementation']['entry']['path'], 'exec'), namespace)
    namespace['authorize'](dict(path=L['request_path'],bytes=len(qb),sha256=QH),dict(path=L['authorization_path'],bytes=Path(L['authorization_path']).stat().st_size,sha256=auth_sha),dict(path=L['runtime_path'],bytes=Path(L['runtime_path']).stat().st_size,sha256=runtime_sha))
    launch = namespace['render_launcher'](q, QH, auth_sha, runtime_sha)
    need(max(map(len, launch.splitlines())) <= 2048 and '\\' not in launch.replace('\\n', ''), 'launcher lines/POSIX contract')
    with clean(L['launcher_path']).open('xb') as f:
        f.write(launch.encode('utf-8')); f.flush(); os.fsync(f.fileno())
    os.chmod(L['launcher_path'], 0o700)
    subprocess.run(['/bin/bash', '-n', L['launcher_path']], check=True, timeout=5)
    need(not out.exists() and time.monotonic()-START <= 120, 'last output/time gate')
    session_absent(L['tmux_session']); smi(I)
    emit(q['launch_attempt'], dict(status='CLAIMED_BEFORE_TMUX', request_sha256=QH))
    stage('single_attempt_claimed_before_tmux')
    result = subprocess.run(['tmux', 'new-session', '-d', '-s', L['tmux_session'], '-c', str(PROJECT),
                             '/bin/bash '+shlex.quote(L['launcher_path'])], capture_output=True, timeout=10)
    need(result.returncode == 0, 'tmux startup failed: '+repr(result.stderr[:512]))
    time.sleep(2)
    live = subprocess.run(['tmux', 'has-session', '-t', L['tmux_session']], capture_output=True, timeout=5).returncode == 0
    receipt = dict(status='AUTHORIZED_SINGLE_LAUNCH_RETURNED_INSPECT_STARTUP', request_sha256=QH,
        tmux_returncode=result.returncode, session=L['tmux_session'], session_present=live,
        authorization_sha256=auth_sha, runtime_sha256=runtime_sha, launcher_sha256=sha(L['launcher_path']),
        output=str(out), exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,
        log_tail=Path(L['log']).read_text(errors='replace')[-7000:] if Path(L['log']).exists() else None)
    emit(control/'startup_receipt_v1.json', receipt); print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        failure = dict(status='AUTHORIZED_OPERATION_FAILED_STOP_NO_RETRY', phase=PHASE,
                       error=repr(exc), hashed_bytes=READ, seconds=time.monotonic()-START,
                       installation_root_exists=INSTALL.exists())
        control = INSTALL/'control'
        if control.is_dir() and not (control/'operation_failure_v1.json').exists():
            emit(control/'operation_failure_v1.json', failure)
        print(json.dumps(failure), flush=True)
        raise
