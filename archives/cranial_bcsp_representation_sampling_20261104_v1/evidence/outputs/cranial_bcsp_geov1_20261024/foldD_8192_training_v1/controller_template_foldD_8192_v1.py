"""Frozen controller template; substituted inputs must originate from read_bytes/Base64."""
import base64, datetime, hashlib, json, os, shlex, shutil, socket, stat, subprocess, time
from pathlib import Path
SCOPE_SHA = '__EXECUTION_SCOPE_SHA256__'
SCOPE_RAW = base64.b64decode('__EXECUTION_SCOPE_RAW_BASE64__', validate=True)
Q_RAW = base64.b64decode('__ENTRY_REQUEST_RAW_BASE64__', validate=True)
ACCEPT_RAW = base64.b64decode('__MIGRATION_ACCEPTANCE_RAW_BASE64__', validate=True)
USER_GRANT = base64.b64decode('__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__', validate=True).decode('utf-8')
START = time.monotonic()
created, created_dirs = [], []
phase = 'FROZEN_REQUEST'
tmux_attempted = False

def need(ok, reason):
    if not ok:
        raise RuntimeError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def jraw(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def event(value):
    print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)

def budget():
    need(time.monotonic() - START < 110, 'controller time budget')

def parents(p):
    for a in reversed(p.parents):
        if os.path.lexists(a):
            need(stat.S_ISDIR(a.lstat().st_mode), 'invalid/link parent: ' + str(a))

def absent(p):
    parents(p)
    need(not os.path.lexists(p), 'existing execution path: ' + str(p))

def exact(r):
    budget()
    p = Path(r['path'])
    parents(p)
    st = p.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size == r['bytes'], 'bound type/size: ' + str(p))
    raw = p.read_bytes()
    after = p.stat()
    need((st.st_ino, st.st_size, st.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns),
         'bound file changed: ' + str(p))
    need(sha(raw) == r['sha256'], 'bound hash: ' + str(p))
    return raw

def secure_dir(p):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in p.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise

def create_dir(p):
    absent(p)
    fd = secure_dir(p.parent)
    try:
        os.mkdir(p.name, 0o700, dir_fd=fd)
        created_dirs.append(str(p))
    finally:
        os.close(fd)

def create_file(p, raw, mode=0o600):
    absent(p)
    fd = secure_dir(p.parent)
    try:
        child = os.open(p.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=fd)
        created.append(str(p))
        with os.fdopen(child, 'wb') as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    r = dict(path=str(p), bytes=len(raw), sha256=sha(raw))
    exact(r)
    return r

def cmd(args, timeout=10):
    r = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return dict(returncode=r.returncode, stdout=r.stdout.decode('utf-8'), stderr=r.stderr.decode('utf-8'))

def tail(p, size=8192):
    if not p.is_file() or p.is_symlink():
        return ''
    with p.open('rb') as stream:
        stream.seek(max(0, p.stat().st_size-size))
        return stream.read(size).decode('utf-8', errors='replace')

try:
    need(sha(SCOPE_RAW) == SCOPE_SHA, 'authorized execution scope hash')
    scope = json.loads(SCOPE_RAW)
    q, accept = json.loads(Q_RAW), json.loads(ACCEPT_RAW)
    need(scope['status'] == q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION'
         and scope['execution_authorized'] is False, 'immutable pending requests')
    for key, raw in [('entry_request', Q_RAW), ('migration_acceptance', ACCEPT_RAW)]:
        need(len(raw) == scope[key]['bytes'] and sha(raw) == scope[key]['sha256'], key + ' binding')
    need(accept['authorizes_only_pending_request_creation'] is True
         and accept['is_training_execution_authorization'] is False
         and accept['new_gpu_execution_validated'] is False, 'migration acceptance boundaries')
    need(q['run_id'] == scope['run_id'] and q['fold'] == 'D' and q['n_input'] == 8192, 'single frozen run')
    paths = scope['future_paths']
    project = Path(q['identity']['project'])
    control = Path(paths['entry_request']).parent
    output = Path(paths['output'])
    identity = q['identity']
    phase = 'IDENTITY_RESOURCE_FRESHNESS'
    need(socket.gethostname() == identity['hostname'] and os.getuid() == identity['uid'], 'hostname/uid')
    parents(project)
    need(stat.S_ISDIR(project.lstat().st_mode), 'project directory')
    os.chdir(project)
    need(str(Path.cwd()) == str(project), 'cwd')
    py = Path(identity['python_realpath'])
    exact(dict(path=str(py), bytes=17331920,
               sha256='01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'))
    version = cmd([str(py), '-I', '-S', '-B', '--version'], 5)
    need(version['returncode'] == 0 and (version['stdout']+version['stderr']).strip() == 'Python 3.10.20',
         'fixed Python version')
    gpu = cmd(['/usr/bin/nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total,memory.used',
               '--format=csv,noheader,nounits'])
    need(gpu['returncode'] == 0 and len(gpu['stdout'].strip().splitlines()) == 1, 'one GPU query')
    v = [x.strip() for x in gpu['stdout'].strip().split(',')]
    need(v[:4] == [identity['gpu_uuid'], identity['gpu_name'], identity['driver_version'],
                   str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4]) <= 256,
         'GPU identity/idle')
    processes = cmd(['/usr/bin/nvidia-smi', '--query-compute-apps=gpu_uuid,pid',
                     '--format=csv,noheader,nounits'])
    need(processes['returncode'] == 0 and not processes['stdout'].strip(), 'no other compute process')
    free = shutil.disk_usage(project).free
    need(free >= scope['resources_unchanged']['static']['minimum_free_disk_bytes'], 'disk reserve')
    absent(control)
    absent(output)
    for key in ('execution_scope', 'migration_acceptance', 'entry_request', 'authorization',
                'runtime', 'launcher', 'launch_attempt'):
        need(Path(paths[key]).parent == control, 'exact control parent')
        absent(Path(paths[key]))
    need(os.access(control.parent, os.W_OK | os.X_OK)
         and os.access(output.parent, os.W_OK | os.X_OK), 'owned parents writable')
    session = paths['tmux_session']
    session_probe = cmd(['/usr/bin/tmux', 'has-session', '-t', session], 5)
    need(session_probe['returncode'] == 1, 'unused tmux session')
    phase = 'FROZEN_IMPLEMENTATION_DATA_ASSETS'
    records = [q['static_config'], q['order_plan'], q['GPU_audit'], q['preflight_scope'],
               q['resource_rebind'], *q['implementation'].values(), q['QC']['qualified_receipt'],
               q['QC']['verification'], q['QC']['fold_binding'], *q['QC']['manifests'].values()]
    blobs = {r['path']: exact(r) for r in records}
    config = json.loads(blobs[q['static_config']['path']])
    need(config['resources'] == scope['resources_unchanged']['static']
         and config['counts'] == dict(cases=315, sources=63, batch=8, epochs=100,
                                      batches_per_epoch=39, updates=3900, exposures=31200),
         'frozen resource/count contract')
    rebind = json.loads(blobs[q['resource_rebind']['path']])
    need(rebind['new_identity'] == identity and rebind['new_gpu_execution_validated'] is False
         and rebind['historical_GPU_evidence_only'] is True, 'rebound metadata')
    rr = dict(rebind['new_readonly_report'])
    rr['path'] = str(Path(q['resource_rebind']['path']).parent / rr['path'])
    readonly_report = json.loads(exact(rr))
    assets_checked = []
    for r in readonly_report['frozen_assets']['manifest']:
        frozen = dict(path=r['path'], bytes=r['expected_bytes'], sha256=r['expected_sha256'])
        exact(frozen)
        assets_checked.append(frozen)
    need(len(assets_checked) == 30, 'exact selected assets')
    qualified = json.loads(blobs[q['QC']['qualified_receipt']['path']])
    need(qualified['verification'] == q['QC']['verification']
         and qualified['manifests'] == q['QC']['manifests']
         and qualified['fold_binding'] == q['QC']['fold_binding']
         and qualified['fold'] == 'D' and qualified['n_input'] == 8192,
         'qualified QC exact paths')
    folds = json.loads(blobs[q['QC']['fold_binding']['path']])['folds']['D']
    ids, sources = folds['train_case_ids'], folds['train_sources']
    need(len(ids) == len(set(ids)) == 315 and len(sources) == len(set(sources)) == 63
         and not set(sources) & set(folds['dev_sources']), 'fixed train sources')
    need(sha(('\n'.join(ids)+'\n').encode()) == qualified['train_allowlist_sha256'], 'train allowlist')
    manifest = {r['case_id']: r for r in
                (json.loads(line) for line in blobs[q['QC']['manifests']['8192']['path']].decode().splitlines())}
    need(len(manifest) == 420, 'manifest metadata count')
    counts = {source: 0 for source in sources}
    payload_bytes = 0
    data_root = Path(q['data_root'])
    for cid in ids:
        budget()
        r = manifest[cid]
        need(r['source_id'] in counts and r['n_input'] == r['n_target'] == 8192
             and r['normalization_source'] == 'defective_bbox', 'training data metadata')
        counts[r['source_id']] += 1
        p = data_root / r['point_path']
        need(data_root in p.parents and p.suffix == '.npz', 'explicit payload boundary')
        parents(p)
        st = p.lstat()
        need(stat.S_ISREG(st.st_mode) and 0 < st.st_size < 4194304, 'payload type/size: ' + str(p))
        exact(dict(path=str(p), bytes=st.st_size, sha256=r['sha256']))
        payload_bytes += st.st_size
    need(set(counts.values()) == {5} and payload_bytes == 49417378, 'fixed315 payload bytes/sources')
    plan = json.loads(blobs[q['order_plan']['path']])
    need(plan['case_ids'] == ids and len(plan['epochs']) == 100, 'authoritative order identity')
    for epoch, row in enumerate(plan['epochs']):
        batches = row['batches']
        flat = [x for batch in batches for x in batch] + row['dropped']
        need(row['epoch'] == epoch and len(batches) == 39 and all(len(b) == 8 for b in batches)
             and len(row['dropped']) == 3 and len(flat) == len(set(flat)) == 315
             and set(flat) == set(ids), 'shared order counts')
    # Last metadata freshness check immediately before any control write.
    absent(control)
    absent(output)
    need(cmd(['/usr/bin/tmux','has-session','-t',session],5)['returncode'] == 1, 'tmux became occupied')
    event(dict(status='TRAIN_PREWRITE_CHECKS_PASS', scope_sha256=SCOPE_SHA,
               hostname=socket.gethostname(), GPU_header=v, free_bytes=free,
               bound_records=len(records), selected_assets=30, train_payloads=315,
               payload_bytes=payload_bytes, server_writes_so_far=0))
    phase = 'MATERIALIZE_ONE_WAY'
    create_dir(control)
    materialized = []
    for key, raw in [('execution_scope', SCOPE_RAW), ('migration_acceptance', ACCEPT_RAW),
                     ('entry_request', Q_RAW)]:
        materialized.append(create_file(Path(paths[key]), raw))
    grant_text = ('\u7528\u6237\u539f\u6587\uff1a' + USER_GRANT + '\n\u6388\u6743\u4e0a\u4e0b\u6587 execution_scope_sha256=' + SCOPE_SHA
                  + '\n\u5165\u53e3 request_sha256=' + sha(Q_RAW))
    auth = dict(schema='bcsp-training-authorization-v1', request_sha256=sha(Q_RAW),
                explicit_user_authorization=True, user_authorization_text=grant_text)
    auth_raw = jraw(auth)
    auth_record = create_file(Path(paths['authorization']), auth_raw)
    materialized.append(auth_record)
    runtime = dict(schema='bcsp-training-runtime-v1', request_sha256=sha(Q_RAW),
                   authorization_sha256=auth_record['sha256'])
    runtime_raw = jraw(runtime)
    runtime_record = create_file(Path(paths['runtime']), runtime_raw)
    materialized.append(runtime_record)
    argv = scope['future_materialization_contract']['external_training_argv']
    argv = [auth_record['sha256'] if x == '<computed_authorization_SHA256>' else
            runtime_record['sha256'] if x == '<computed_runtime_SHA256>' else x for x in argv]
    need(argv[:4] == ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s'], 'external timeout')
    lines = ['#!/usr/bin/env bash', 'set -u', 'set -o pipefail', 'set -o noclobber', 'umask 077',
             'cd ' + shlex.quote(str(project)) + ' || exit 65']
    for k, venv in scope['environment'].items():
        lines.append('export ' + k + '=' + shlex.quote(venv))
    for record in (materialized[2], auth_record, runtime_record):
        lines.append('[ "$(sha256sum -- ' + shlex.quote(record['path'])
                     + ' | cut -d \' \' -f 1)" = ' + shlex.quote(record['sha256']) + ' ] || exit 65')
    lines += ['mkdir -- ' + shlex.quote(str(output)) + ' || exit 73',
              '[ -d ' + shlex.quote(str(output)) + ' ] && [ ! -L '
              + shlex.quote(str(output)) + ' ] || exit 73',
              'set +e', shlex.join(argv) + ' > ' + shlex.quote(paths['log']) + ' 2>&1',
              'training_rc=$?', 'printf \'%s\\n\' "$training_rc" > ' + shlex.quote(paths['exit_code']),
              'save_rc=$?', '[ "$save_rc" -eq 0 ] || exit 74', 'exit "$training_rc"']
    launcher_raw = ('\n'.join(lines) + '\n').encode('utf-8')
    materialized.append(create_file(Path(paths['launcher']), launcher_raw, 0o700))
    phase = 'CLAIM_SINGLE_LAUNCH'
    absent(output)
    need(cmd(['/usr/bin/tmux','has-session','-t',session],5)['returncode'] == 1, 'tmux collision before claim')
    marker = dict(status='CLAIMED_BEFORE_TMUX', request_sha256=sha(Q_RAW),
                  execution_scope_sha256=SCOPE_SHA,
                  UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(), automatic_retry=False)
    materialized.append(create_file(Path(paths['launch_attempt']), jraw(marker)))
    event(dict(status='TRAIN_MATERIALIZED_AND_ATTEMPT_CLAIMED', files=materialized,
               auth_content_base64=base64.b64encode(auth_raw).decode(),
               runtime_content_base64=base64.b64encode(runtime_raw).decode(),
               launcher_content_base64=base64.b64encode(launcher_raw).decode()))
    phase = 'TMUX_SINGLE_START'
    tmux_attempted = True
    launch = cmd(['/usr/bin/tmux','new-session','-d','-s',session,
                  'bash ' + shlex.quote(paths['launcher'])],10)
    need(launch['returncode'] == 0, 'tmux start nonzero: ' + launch['stderr'])
    phase = 'READONLY_STARTUP_CONFIRMATION'
    deadline = time.monotonic() + 30
    state = {}
    while time.monotonic() < deadline:
        budget()
        session_state = cmd(['/usr/bin/tmux','has-session','-t',session],5)
        pid_path = Path(paths['worker_pid'])
        pid = int(pid_path.read_text().strip()) if pid_path.is_file() and not pid_path.is_symlink() else None
        worker_live = False
        if pid is not None:
            proc = Path('/proc') / str(pid)
            if proc.exists():
                worker_live = (str(q['implementation']['entry']['path']).encode()
                               in (proc/'cmdline').read_bytes().split(b'\0'))
        exit_path = Path(paths['exit_code'])
        exit_code = int(exit_path.read_text().strip()) if exit_path.is_file() else None
        last_metric = None
        metric_tail = tail(Path(paths['metrics']))
        if metric_tail.strip():
            try:
                last_metric = json.loads(metric_tail.strip().splitlines()[-1])
            except (ValueError, IndexError):
                pass
        failure_present = any(Path(paths[key]).is_file() for key in ('failure','startup_failure'))
        state = dict(tmux_present=session_state['returncode']==0, worker_pid=pid, worker_live=worker_live,
                     exit_code=exit_code, last_committed_step=last_metric.get('step') if last_metric else None,
                     completion_present=Path(paths['completion']).is_file(), failure_present=failure_present)
        if exit_code is not None or failure_present or last_metric is not None:
            break
        if session_state['returncode'] != 0:
            time.sleep(0.2)
            break
        time.sleep(0.5)
    need(not state.get('failure_present') and state.get('exit_code') in (None, 0),
         'training startup failed: ' + repr(state))
    need((state.get('tmux_present') and state.get('worker_live')) or
         (state.get('exit_code') == 0 and state.get('completion_present')), 'startup not confirmed')
    event(dict(status='TRAINING_STARTED' if state.get('exit_code') is None else 'TRAINING_EXITED_AWAITING_AUDIT',
               state=state, scope_sha256=SCOPE_SHA, paths=paths,
               new_gpu_execution_validated=False, post_training_freeze_audit_performed=False,
               seconds=time.monotonic()-START, UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except BaseException as exc:
    failure = dict(status='FAILED_STOP_NO_RETRY', phase=phase, error=repr(exc),
                   created_files=created, created_directories=created_dirs, tmux_attempted=tmux_attempted,
                   scope_sha256=SCOPE_SHA, no_retry=True, no_resume=True, no_cleanup=True)
    if 'paths' in globals():
        failure['launch_log_tail'] = tail(Path(paths['log']))
        failure['exit_code_text'] = tail(Path(paths['exit_code']),256)
        for key in ('failure','startup_failure'):
            failure[key] = tail(Path(paths[key]))
    event(failure)
    raise
