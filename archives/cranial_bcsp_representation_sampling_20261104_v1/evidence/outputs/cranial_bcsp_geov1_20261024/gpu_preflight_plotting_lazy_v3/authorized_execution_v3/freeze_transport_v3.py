"""Freeze only this authorized 26-file deployment transport; never connect remotely."""
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REQUEST = BASE / 'artificial_gpu_zero_update_execution_request_v3.json'
REQUEST_SHA = '7a7a74fcec86bb4fa6c7ab77b74e8d509a26ae75ade73a05d9c8cab183ef2365'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    request_bytes = REQUEST.read_bytes()
    assert sha(request_bytes) == REQUEST_SHA
    q = json.loads(request_bytes)
    assert q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION'
    root = Path(q['future_control_paths']['request']).as_posix().split('/evidence/')[0] + '/'
    files = []
    for row in q['future_limited_deployment']['files']:
        data = Path(row['local_source']).read_bytes()
        assert len(data) == row['bytes'] and sha(data) == row['sha256']
        assert row['server_target'].startswith(root)
        files.append((row['server_target'][len(root):], data))
    files.append(('evidence/execution_request_v3.json', request_bytes))
    for name in ('authorization_v3.json', 'runtime_v3.json', 'launcher_v3.sh'):
        files.append(('control/' + name, (HERE / name).read_bytes()))
    auth = json.loads((HERE / 'authorization_v3.json').read_bytes())
    runtime = json.loads((HERE / 'runtime_v3.json').read_bytes())
    assert auth['request_sha256'] == REQUEST_SHA and auth['explicit_user_authorization'] is True
    assert 'runtime_sha256' not in auth
    assert runtime == {'schema': 'bcsp-preflight-runtime-v1', 'request_sha256': REQUEST_SHA,
                       'authorization_sha256': sha((HERE / 'authorization_v3.json').read_bytes())}
    script = (HERE / 'launcher_v3.sh').read_text(encoding='utf-8')
    ast.parse(script.split("<<'PY'\n", 1)[1].split('\nPY\n', 1)[0])
    assert 'record_exit()' in script and 'rc=$?' in script and 'trap record_exit EXIT' in script
    assert '--kill-after=5s' in script and '900s' in script and 'set -C' in script
    assert '\r' not in script and script.count('bcsp_artificial_gpu_preflight_v3.py') == 1
    assert len(files) == len({name for name, data in files}) == 26
    for name, data in files:
        assert not name.startswith('/') and '..' not in Path(name).parts and data
    out = HERE / 'transport_v3'
    assert not out.exists(), 'refuse existing transport output'
    out.mkdir()
    archive = out / 'bcsp_gpu_preflight_v3.tar.gz'
    with archive.open('xb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as tar:
                for name, data in sorted(files):
                    info = tarfile.TarInfo(name)
                    info.size, info.mode, info.mtime = len(data), 0o644, 0
                    tar.addfile(info, io.BytesIO(data))
    manifest = ''.join(sha(data) + '  ' + name + '\n' for name, data in sorted(files)).encode('ascii')
    sidecars = {
        'bcsp_gpu_preflight_v3.tar.gz.sha256': (sha(archive.read_bytes()) + '  ' + archive.name + '\n').encode(),
        'bcsp_gpu_preflight_v3.contents.sha256': manifest,
        'bcsp_gpu_preflight_v3.contents.sha256.sha256': (sha(manifest) + '  bcsp_gpu_preflight_v3.contents.sha256\n').encode(),
        'bcsp_gpu_preflight_v3.bytes': (str(archive.stat().st_size) + '\n').encode()
    }
    for name, data in sidecars.items():
        with (out / name).open('xb') as f:
            f.write(data)
    # Read-only archive verification; no extraction, script execution or model imports.
    expected = dict(files)
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        assert len(members) == 26 and all(m.isfile() for m in members)
        assert {m.name for m in members} == set(expected)
        for member in members:
            assert tar.extractfile(member).read() == expected[member.name]
    print(json.dumps({'status': 'TRANSPORT_FROZEN_NOT_UPLOADED_NOT_DEPLOYED', 'members': len(files),
                      'files': [{'filename': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                                for p in sorted(out.iterdir())]}, indent=2))

if __name__ == '__main__':
    main()
