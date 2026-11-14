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

QH = 'b616a762783fd4f43af4467c6c47e41e73aa40a24fac223317e710ee7372825e'
AH = 'a0fa5d856857fc5ed28d43fcfa95e68ee861ce04f71ca5ce157597ef9147034a'
ARCHIVE = Path('/home/jovyan/bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz')
INSTALL = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1')
PROJECT = Path('/home/jovyan/adapointr_work/PoinTr')
START = time.monotonic()
READ = 0
PHASE = 'start'
ROWS = []
FROZEN_TARGETS = [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/bcsp_lqi_training_entry_v1.py', 'bytes': 21204, 'sha256': 'd623a2c5d206faccbf348c2130a73cb00ff44e41f5ad6b543a5fb8cf9b86ab06'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/bcsp_lqi_runtime_adapter_v1.py', 'bytes': 2185, 'sha256': '37946f9f04e20718adee4fe2559ffe9bc3446977d3341197bca19600e6064a8c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/native_LQI_admission_receipt_v1.json', 'bytes': 2192, 'sha256': '5bcb2cff36e02e14acd4609e601fbc6d63aa776489ea2dda1b887f6b180de770'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/formal_post_CUDA_freeze_audit_result_v1.json', 'bytes': 4624, 'sha256': 'bd7aa09346f26897ca375fca8c6ccc3b6b9d119421d60f8943a767440d1e1ca9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/construction.json', 'bytes': 86245, 'sha256': 'a8d4c769f34304f6906dd26d080f53f1976bfea05f76649142c6e7fedf5fe3fd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/completion.json', 'bytes': 1903, 'sha256': 'd2797e3e6cb5b37104f5d21e2f57d32ee7a7b2eb8c9f8dc65e5610375b47d644'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/LQI_artificial_cuda_execution_request_v1.json', 'bytes': 13482, 'sha256': 'd1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/FoldC_readiness_receipt_v1.json', 'bytes': 70346, 'sha256': 'de9f5ed1880ab48b78e1038cdc955738da021c284c025cfc46249ee602289362'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/LQI_CD_training_contract_v1.json', 'bytes': 3029, 'sha256': '9b338de67f3ae62fa384efe3d4163bea5551b4155cf6137bb1b1348b13eac172'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/training_entry_P3_v1.json', 'bytes': 3291, 'sha256': 'e94a5633ea1e5d97ee34e75911d717ccf29bf10207a38702b585d6e9dca9210e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/LQI_FoldC_training_execution_request_v1.json', 'bytes': 13515, 'sha256': 'b616a762783fd4f43af4467c6c47e41e73aa40a24fac223317e710ee7372825e'}]


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
    exact(dict(path=str(ARCHIVE), bytes=36487, sha256=AH))
    for record in [{'path': '/home/jovyan/bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.sha256', 'bytes': 118, 'sha256': 'ca88189994ffd8a7ce5c95f5f6e4db7a4187d10a5f41a9d4976860acc7730bdd'}, {'path': '/home/jovyan/bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.bytes', 'bytes': 7, 'sha256': '5899b3945d0d59f003283c4f2b01d5b4a0a62a15beccab46c765fb6897f9d7d0'}, {'path': '/home/jovyan/bcsp_lqi_FoldC_training_pending_20261111_v1.tar.gz.contents.sha256', 'bytes': 1096, 'sha256': 'b9942b6b9c2df0a831bb866dda10fa643b154918ed4765f62ecfdcc2bcb547fd'}]:
        exact(record)
    need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0] == AH and
         int(Path(str(ARCHIVE)+'.bytes').read_text()) == 36487, 'archive sidecars')
    payload = {}
    with tarfile.open(ARCHIVE, 'r:gz') as tar:
        members = tar.getmembers(); need(len(members) == 11, 'eleven members')
        for member in members:
            need(member.isfile() and member.name == Path(member.name).name and member.name not in payload
                 and member.size <= 2*1024**2, 'archive member boundary')
            payload[member.name] = tar.extractfile(member).read()
    qb = payload['LQI_FoldC_training_execution_request_v1.json']
    need(hashlib.sha256(qb).hexdigest() == QH, 'explicitly authorized request hash')
    q = json.loads(qb); I = q['identity']; L = q['launch_contract']; out = clean(q['output'])
    need(Path(q['implementation']['entry']['path']).parent == INSTALL and I['project'] == str(PROJECT), 'frozen roots')
    need(str(Path(sys.executable).resolve()) == I['python_realpath'] and sys.version.split()[0] == I['python_version'], 'Python identity')
    expected = {Path(r['path']).name: r for r in FROZEN_TARGETS}
    expected['LQI_FoldC_training_execution_request_v1.json'] = dict(path=L['request_path'], bytes=len(qb), sha256=QH)
    need(set(payload) == set(expected) and len(expected) == 11, 'exact installation set')
    for name, r in expected.items():
        need(clean(r['path']).parent == INSTALL and len(payload[name]) == r['bytes']
             and hashlib.sha256(payload[name]).hexdigest() == r['sha256'], 'member binding: '+name)
    listing = ''.join(hashlib.sha256(blob).hexdigest()+'  '+name+'\n' for name, blob in payload.items())
    need(Path(str(ARCHIVE)+'.contents.sha256').read_text() == listing, 'exact content sidecar')
    need(not clean(INSTALL).exists() and not out.exists() and INSTALL.parent.is_dir() and PROJECT.is_dir(), 'fresh safe parents')
    session_absent(L['tmux_session']); smi(I)
    need(shutil.disk_usage(PROJECT).free >= json.loads(exact(q['static_config']).read_bytes())['resources']['minimum_free_disk_bytes'], 'disk budget')
    stage('reused_source_provider_and_extension_hashes')
    for r in [q['preflight_scope'],q['static_config'],q['order_plan'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*[v for k,v in q['implementation'].items() if k not in ('entry','bridge')],*q['dependencies']]:
        exact(r)
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
    selected,fold=metadata.verify_qualified_receipt(json.loads(Path(q['QC']['qualified_receipt']['path']).read_bytes()),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
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
    emit(control/'readiness_and_installation_receipt_v1.json', dict(status='ELEVEN_EXCLUSIVE_INSTALL_HASHES_PASS',
         request_sha256=QH, archive_sha256=AH, targets=[expected[n] for n in payload],
         read_manifest=ROWS, verification_seconds=time.monotonic()-START,
         training_payload_files_hashed=315, payload_arrays_read=0, checkpoint_reads=0, overwritten_files=0))
    stage('materialize_one_way_authorization_runtime_launcher')
    auth = dict(schema='bcsp-lqi-training-authorization-v1', request_sha256=QH, explicit_user_authorization=True,
                user_authorization_text='2026-11-11: In reply to the complete request SHA256 '+QH+
                ', user explicitly answered: 已上传，单独授权此request完整SHA256，才能不覆盖安装并启动唯一一次Fold C训练. Exactly Fold C 8k/8k 3900 steps. Failure stops, no retry/resume/BNCal/evaluation.')
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
