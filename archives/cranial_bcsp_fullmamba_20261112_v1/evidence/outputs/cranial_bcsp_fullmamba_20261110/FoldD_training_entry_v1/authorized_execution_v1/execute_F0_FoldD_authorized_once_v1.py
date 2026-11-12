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

QH = 'ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0'
AH = 'fd5801178d821594ce212dcaa39a5b9d5bfd079d5ca5838b10a5e9e638a62440'
ARCHIVE = Path('/home/jovyan/bcsp_f0_FoldD_training_pending_20261110_v1.tar.gz')
INSTALL = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1')
PROJECT = Path('/home/jovyan/adapointr_work/PoinTr')
START = time.monotonic()
READ = 0
PHASE = 'start'
ROWS = []
FROZEN_TARGETS = [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/bcsp_f0_foldD_training_entry_v1.py', 'bytes': 24087, 'sha256': '42b2e2cc83bce24a301b675e863e19b5d62e28311fae2d327f5b54792391cf8c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/bcsp_f0_runtime_adapter_v1.py', 'bytes': 2183, 'sha256': '6c74ae2fdfcf4d835399c128fef6eff005707f0ef081edc683a349f21eef0e49'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/native_admission_receipt_v2.json', 'bytes': 2587, 'sha256': 'ff47195c2456c2746ec9ae58cf266bc004375d5f79d87b8e536fa6ab549cf1c0'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/post_CUDA_freeze_audit_result_v2.json', 'bytes': 14441, 'sha256': '7ef059444d071ee7f59d6403504e89735a4949329fe8ea5fcba1102c7d41ffab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/construction.json', 'bytes': 86021, 'sha256': '27fdca4cf55aaa6bf0c5c20f76d141952a59c0327334f0dcae718bc8d7a01ee9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/completion.json', 'bytes': 1918, 'sha256': 'd07b6cfd790de204fba10fc9196786fadaf33e51865fe6fd59fdbfd70e43fd36'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/F0_artificial_cuda_execution_request_v1.json', 'bytes': 15385, 'sha256': 'a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/post_training_freeze_audit_result_v1.json', 'bytes': 16382, 'sha256': 'd2e98602b245596268eb288ee5adcfb85d4f95975e7463a3e7c280563299c958'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/F0_FoldC_training_execution_request_v1.json', 'bytes': 13468, 'sha256': 'afd2750a3738f65d6fcfc308153c4358a4ded5e242a7e74796f9d8dec519d32d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/model_construction.json', 'bytes': 85327, 'sha256': 'c7895bf960a49dac0a7e578f7ff0fa3c69d46cfe7013385b02df144bd6abe005'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/initialization.json', 'bytes': 289, 'sha256': 'd699537dfe3d8cabfcbfacdfd1bb4a07d5c555cb1a5c0f6b731acb5139684aa6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/order_plan.json', 'bytes': 1248506, 'sha256': '6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/FoldC_completion.json', 'bytes': 558, 'sha256': '91880af47d81158c86312b36638171cf31e41c1fe6265193ccf8d064820b713c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/frozen_M0_FoldD_reference_request_v1.json', 'bytes': 15823, 'sha256': '55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/FoldD_readiness_receipt_v1.json', 'bytes': 70341, 'sha256': '3a09bf142e0c0f35c8d832a5a9fec346b7caedee7b27c4171f3a88ed865e4126'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/F0_CD_training_contract_v1.json', 'bytes': 4899, 'sha256': '75fe3e8c462879885c64a9d3f38ab25c1e059598caf34325b2ac66a3b1d8edc9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/training_entry_P3_v1.json', 'bytes': 2846, 'sha256': '1eae85117d3a32ce535d6f602876f1a44be456e6b426dc8f18fa883f03f2d68b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/F0_FoldD_training_execution_request_v1.json', 'bytes': 15345, 'sha256': 'ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0'}]


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
    need(socket.gethostname() == 'shu-common-25721452-notebook-n8xph5-0' and os.getuid() == 1000, 'identity')
    exact(dict(path=str(ARCHIVE), bytes=142281, sha256=AH))
    for record in [{'path': '/home/jovyan/bcsp_f0_FoldD_training_pending_20261110_v1.tar.gz.sha256', 'bytes': 117, 'sha256': '98ceb2b801558d4b9da9103937964b70f5e5fd2ab029b7ef3cdc499d7949d6d6'}, {'path': '/home/jovyan/bcsp_f0_FoldD_training_pending_20261110_v1.tar.gz.bytes', 'bytes': 8, 'sha256': '3144cef2bf7f1af6d901fe17745fd430a46dd624fe5ee68f7d7a7eb1fe74b0dc'}, {'path': '/home/jovyan/bcsp_f0_FoldD_training_pending_20261110_v1.tar.gz.contents.sha256', 'bytes': 1765, 'sha256': 'de26874f94217f64183ba9f9934b07ce23dae5922d142144d72ac5c334f7a85a'}]:
        exact(record)
    need(Path(str(ARCHIVE)+'.sha256').read_text().split()[0] == AH and
         int(Path(str(ARCHIVE)+'.bytes').read_text()) == 142281, 'archive sidecars')
    payload = {}
    with tarfile.open(ARCHIVE, 'r:gz') as tar:
        members = tar.getmembers(); need(len(members) == 18, 'eighteen members')
        for member in members:
            need(member.isfile() and member.name == Path(member.name).name and member.name not in payload
                 and member.size <= 2*1024**2, 'archive member boundary')
            payload[member.name] = tar.extractfile(member).read()
    qb = payload['F0_FoldD_training_execution_request_v1.json']
    need(hashlib.sha256(qb).hexdigest() == QH, 'explicitly authorized request hash')
    q = json.loads(qb); I = q['identity']; L = q['launch_contract']; out = clean(q['output'])
    need(Path(q['implementation']['entry']['path']).parent == INSTALL and I['project'] == str(PROJECT), 'frozen roots')
    need(str(Path(sys.executable).resolve()) == I['python_realpath'] and sys.version.split()[0] == I['python_version'], 'Python identity')
    expected = {Path(r['path']).name: r for r in FROZEN_TARGETS}
    expected['F0_FoldD_training_execution_request_v1.json'] = dict(path=L['request_path'], bytes=len(qb), sha256=QH)
    need(set(payload) == set(expected) and len(expected) == 18, 'exact installation set')
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
    emit(control/'readiness_and_installation_receipt_v1.json', dict(status='EIGHTEEN_EXCLUSIVE_INSTALL_HASHES_PASS',
         request_sha256=QH, archive_sha256=AH, targets=[expected[n] for n in payload],
         read_manifest=ROWS, verification_seconds=time.monotonic()-START,
         training_payload_files_hashed=315, payload_arrays_read=0, checkpoint_reads=0, overwritten_files=0))
    stage('materialize_one_way_authorization_runtime_launcher')
    auth = dict(schema='bcsp-f0-training-authorization-v1',request_sha256=QH,explicit_user_authorization=True,
        user_authorization_text='2026-11-11: User uploaded the package and wrote: 已上传，单独明确授权该完整哈希，才能核验、不覆盖安装并启动唯一一次 Fold D、8k→8k、3900步训练. Referenced complete request SHA256 '+QH+'. One attempt, stop on failure, no retry/resume/BNCal/evaluation.')
    emit(L['authorization_path'], auth); auth_sha = sha(L['authorization_path'])
    runtime = dict(schema='bcsp-f0-training-runtime-v1', request_sha256=QH, authorization_sha256=auth_sha)
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
