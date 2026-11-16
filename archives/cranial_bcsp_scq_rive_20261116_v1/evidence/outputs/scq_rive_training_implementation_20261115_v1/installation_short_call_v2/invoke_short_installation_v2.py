"""Local invocation only. Requires a new explicit installation-attempt authorization.

No connection or write occurs on import. This is not a training launcher.
"""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def emit(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write('\n')


def notice(**value):
    print(json.dumps(value, ensure_ascii=True), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-installation', action='store_true')
    parser.add_argument('--user-authorization', required=True)
    args = parser.parse_args()
    require(args.execute_installation and bool(args.user_authorization.strip()),
            'Separate user authorization for one new installation attempt required')
    calls = json.loads((HERE / 'callset_v2.json').read_bytes())
    require(digest(__file__) == calls['local_driver_sha256'], 'Local driver byte drift')
    require(calls['status'] == 'AWAITING_SEPARATE_INSTALLATION_ATTEMPT_AUTHORIZATION',
            'Pending new attempt only')
    require([row['stage'] for row in calls['calls']] == ['A', 'B', 'C'], 'A/B/C order')
    for row in calls['calls']:
        require(digest(HERE / row['source_name']) == row['source_sha256'], 'Source byte drift')
        require(len(row['command'].encode('utf-8')) <= 2048, 'Bounded command')
    for record in calls['frozen_local_inputs']:
        path = Path(record['path'])
        require(path.stat().st_size == record['bytes'] and digest(path) == record['sha256'],
                'Frozen request, archive, sidecar or mapping drift')
    run = HERE / 'authorized_attempt_v1'
    run.mkdir(exist_ok=False)
    emit(run / 'single_attempt_claim_v1.json', {
        'status': 'CLAIMED_NEW_SINGLE_INSTALLATION_ATTEMPT',
        'user_authorization': args.user_authorization,
        'callset_sha256': digest(HERE / 'callset_v2.json'),
        'request_sha256': calls['request_sha256'],
    })
    started = time.monotonic()
    previous = None
    passed = []
    try:
        for row in calls['calls']:
            now = time.monotonic()
            require(previous is None or now - previous <= 10., 'Precheck gap exceeded10s')
            remaining = 60. - (now - started)
            require(remaining > 0, 'Original cumulative60s installation budget')
            require(passed == list(row['requires']), 'Prior read-only stages must pass')
            require(digest(HERE / row['source_name']) == row['source_sha256'], 'Stage source drift')
            stage = row['stage']
            remote_budget = min(row['remote_timeout_seconds'], int(remaining))
            require(remote_budget > 0, 'No remote time remaining')
            require(stage != 'C' or remote_budget >= 20,
                    'Do not begin writes without the complete20s write budget')
            prefix = '/usr/bin/timeout ' + str(row['remote_timeout_seconds']) + 's '
            require(row['command'].startswith(prefix), 'Exact timeout command prefix')
            remote_command = ('/usr/bin/timeout ' + str(remote_budget) + 's '
                              + row['command'][len(prefix):])
            require(len(remote_command.encode('utf-8')) <= 2048, 'Effective bounded command')
            emit(run / (stage + '_effective_call.json'), {
                'command': remote_command, 'remote_timeout_seconds': remote_budget,
                'local_seconds_remaining': remaining,
            })
            notice(stage=stage, status='STARTING', seconds_remaining=remaining)
            command = ['wsl.exe', '-d', 'Ubuntu-20.04', '--exec',
                       '/home/zhj/.local/bin/hpc5000', 'exec', '--timeout',
                       str(remote_budget + 10), '--', remote_command]
            local_timeout = False
            try:
                result = subprocess.run(command, capture_output=True,
                                        timeout=min(remaining, remote_budget + 15))
                returncode, stdout, stderr = result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired as error:
                returncode, local_timeout = 124, True
                stdout, stderr = error.stdout or b'', error.stderr or b''
            (run / (stage + '_stdout.bin')).write_bytes(stdout)
            (run / (stage + '_stderr.bin')).write_bytes(stderr)
            events = []
            for line in stdout.decode('utf-8', errors='replace').splitlines():
                if line.startswith('{'):
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            emit(run / (stage + '_transport.json'), {
                'returncode': returncode, 'local_timeout': local_timeout,
                'stdout_bytes': len(stdout), 'stderr_bytes': len(stderr),
                'elapsed_seconds': time.monotonic() - started, 'events': events,
            })
            require(returncode == 0 and not local_timeout, 'Stage transport failed: ' + stage)
            require(events and events[-1].get('phase') == row['success_phase'],
                    'Required remote completion not received: ' + stage)
            require(not any(event.get('phase') == 'FAILED_STOP_NO_RETRY' for event in events),
                    'Remote stage failed: ' + stage)
            final = events[-1]
            if stage == 'A':
                require(final['count'] == 58 and final['archive_sha256'] == calls['archive_sha256'],
                        'All58 exact reused hashes and frozen archive required')
            elif stage == 'B':
                require(final['hostname'] == calls['identity']['hostname'] and final['uid'] == 1000
                        and final['targets'] == 11 and final['gpu'] == calls['expected_smi']
                        and final['archive_sha256'] == calls['archive_sha256'], 'Fresh prewrite identity')
            else:
                expected = {r['target']: (r['bytes'], r['sha256']) for r in calls['targets']}
                actual = {r['path']: (r['bytes'], r['sha256']) for r in final['files']}
                require(len(final['files']) == len(actual) == 11 and actual == expected,
                        'Exact11-file installation readback')
                require(final['root'] == calls['install_root'] and not final['controls_created']
                        and final['tests'] == final['forward'] == final['training'] == 0,
                        'No execution outside installation')
            require(time.monotonic() - started <= 60., 'Cumulative60s budget')
            passed.append(stage)
            previous = time.monotonic()
            notice(stage=stage, status='PASS', elapsed_seconds=previous - started)
        emit(run / 'completion_v1.json', {
            'status': 'INSTALLATION_READBACK_PASS_NOT_TRAINING_AUTHORIZATION',
            'passed': passed, 'attempts': 1, 'tests': 0, 'training': 0,
        })
    except BaseException as error:
        emit(run / 'failure_v1.json', {
            'status': 'FAILED_STOP_NO_RETRY', 'error': repr(error),
            'passed': passed, 'elapsed_seconds': time.monotonic() - started,
            'remote_state': 'UNKNOWN_IF_C_WAS_STARTED_ELSE_NO_WRITES_BY_A_B',
            'automatic_retry': False,
        })
        notice(status='FAILED_STOP_NO_RETRY', error=repr(error), passed=passed)
        raise


if __name__ == '__main__':
    main()
