"""One local-only packaging of the exact authorized 327-file scope; no imports/execution of payloads."""
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import time

HERE = Path(__file__).absolute().parent
SCOPE = HERE / 'transport_scope_v1.json'
SCOPE_SHA = '19bb88a4a63484d39a3f42146802af29cc695fc3dbae5ae5488df36046f770c3'
OUT = HERE / 'transport_v1'
NAME = 'bcsp_foldc_8192_train_inputs_v1'
START = time.monotonic()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_time():
    assert time.monotonic() - START <= 120, 'local packaging budget exceeded; stop, do not retry'


def read_source(row):
    check_time()
    p = Path(row['local_source'])
    assert p.is_file() and not any(x.is_symlink() for x in (p, *p.parents)), str(p)
    before = p.stat()
    assert 0 < before.st_size == row['bytes'] <= 4 * 1024**2, str(p)
    data = p.read_bytes()
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ino) == (
        after.st_size, after.st_mtime_ns, after.st_ino), str(p)
    assert digest(data) == row['sha256'], str(p)
    return data


def new_json(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    assert not any(p.is_symlink() for p in (HERE, *HERE.parents))
    assert not OUT.exists() and not (HERE / 'package_attempt_started_v1.json').exists(), 'consumed packaging output'
    raw = SCOPE.read_bytes()
    assert digest(raw) == SCOPE_SHA
    scope = json.loads(raw)
    assert scope['status'] == 'FROZEN_NOT_PACKAGED_NOT_DEPLOYED_NOT_EXECUTION_REQUEST'
    assert scope['is_execution_request'] is False and scope['execution_authorized'] is False
    rows = scope['transport']['files']
    assert len(rows) == 327 and len({r['archive_member'] for r in rows}) == 327
    assert len({r['server_target'] for r in rows}) == 327
    points = [r for r in rows if r['kind'] == 'real_training_point_file']
    assert len(points) == len({r['case_id'] for r in points}) == 315
    assert len({r['source_id'] for r in points}) == 63
    assert sum(r['bytes'] for r in rows) == 51686451 <= 64 * 1024**2
    for row in rows:
        name = PurePosixPath(row['archive_member'])
        assert not name.is_absolute() and '..' not in name.parts and '\\' not in str(name)
        assert row['mode'] == 'create_only_no_overwrite'
        read_source(row)
    new_json(HERE / 'package_attempt_started_v1.json', {
        'scope_sha256': SCOPE_SHA, 'attempts': 1, 'source_files': 327,
        'server_operations': 0, 'package_script_sha256': digest(Path(__file__).read_bytes())})
    OUT.mkdir()
    try:
        archive = OUT / (NAME + '.tar.gz')
        with archive.open('xb') as stream:
            with gzip.GzipFile(filename='', fileobj=stream, mode='wb', compresslevel=6, mtime=0) as zipped:
                with tarfile.open(fileobj=zipped, mode='w', format=tarfile.USTAR_FORMAT) as tar:
                    for row in sorted(rows, key=lambda r: r['archive_member']):
                        data = read_source(row)
                        info = tarfile.TarInfo(row['archive_member'])
                        info.size, info.mode, info.mtime = len(data), 0o644, 0
                        tar.addfile(info, io.BytesIO(data))
        check_time()
        expected = {r['archive_member']: r for r in rows}
        with tarfile.open(archive, 'r:gz') as tar:
            members = tar.getmembers()
            assert len(members) == len({m.name for m in members}) == 327
            assert set(expected) == {m.name for m in members}
            for member in members:
                check_time()
                assert member.isfile() and not member.issym() and not member.islnk()
                row = expected[member.name]
                assert member.size == row['bytes'] and digest(tar.extractfile(member).read()) == row['sha256']
        manifest = ''.join(r['sha256'] + '  ' + r['archive_member'] + '\n'
                           for r in sorted(rows, key=lambda r: r['archive_member'])).encode('ascii')
        h = hashlib.sha256()
        with archive.open('rb') as stream:
            for block in iter(lambda: stream.read(1048576), b''):
                h.update(block)
        sidecars = {
            NAME + '.tar.gz.sha256': (h.hexdigest() + '  ' + archive.name + '\n').encode('ascii'),
            NAME + '.contents.sha256': manifest,
            NAME + '.contents.sha256.sha256': (digest(manifest) + '  ' + NAME + '.contents.sha256\n').encode('ascii'),
            NAME + '.bytes': (str(archive.stat().st_size) + '\n').encode('ascii')}
        for name, data in sidecars.items():
            with (OUT / name).open('xb') as stream:
                stream.write(data)
        assert len(list(OUT.iterdir())) == 5
        assert (OUT / (NAME + '.contents.sha256')).read_bytes() == manifest
        assert (OUT / (NAME + '.tar.gz.sha256')).read_text().split() == [h.hexdigest(), archive.name]
        assert int((OUT / (NAME + '.bytes')).read_text()) == archive.stat().st_size
        check_time()
        result = {
            'status': 'TRANSPORT_VERIFIED_LOCAL_ONLY_NOT_UPLOADED_NOT_DEPLOYED',
            'scope_sha256': SCOPE_SHA, 'members': 327, 'real_point_members': 315,
            'uncompressed_member_bytes': 51686451, 'seconds': time.monotonic() - START,
            'budget_seconds': 120, 'compression': 'gzip level6, mtime0; USTAR regular members, mode0644',
            'verification': 'Every source rehashed; archive reopened and exact member set/size/SHA checked without filesystem extraction or NPZ decoding',
            'atime_excluded_from_source_identity': True,
            'files': [{'filename': p.name, 'local_path': str(p), 'bytes': p.stat().st_size,
                       'sha256': digest(p.read_bytes())} for p in sorted(OUT.iterdir())],
            'server_operations': 0, 'NPZ_decodes': 0, 'model_or_test_calls': 0,
            'execution_request_or_authorization_runtime_launcher_created': False}
        new_json(HERE / 'transport_preparation_receipt_v1.json', result)
        print(json.dumps(result, ensure_ascii=False))
    except BaseException as exc:
        new_json(HERE / 'transport_preparation_failure_v1.json', {
            'status': 'FAILED_STOP_NO_RETRY', 'error': repr(exc), 'scope_sha256': SCOPE_SHA,
            'preserve_partial_output': True, 'server_operations': 0})
        raise


if __name__ == '__main__':
    main()
