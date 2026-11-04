"""Single authorized no-overwrite installation of the exact seven-file monitor overlay."""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import stat
import subprocess
import tarfile
import time

MAP_SHA = '7659ab863df5148c09f59917d9df74a0936b916e09e9f79203368cee37bac9b2'
ARCHIVE_SHA = 'f165a848f59926b608194c18f8a936be7afc7b495e4d5a78bba7d7ebae0d87b4'
NAME = 'bcsp_foldc_8192_monitor_diagnostic_v3_supplement_v1'
UPLOAD_EXPECTED = {
    '.bytes': (6, 'e11e86de8dcbd6b31b5ddcd3d4a02745bcc172a2ae8c9a0a9058c54f011fb80d'),
    '.contents.sha256': (836, '49122bb499463e02330e172aef52622f887e5cc87f08aa01c18b7d64c1995aa6'),
    '.contents.sha256.sha256': (134, '92ff8fb55cdc3fc3d7b790976a5699b39fb81ad317a9504d583792d171b97cfe'),
    '.installation_map.json': (10724, MAP_SHA),
    '.installation_map.json.sha256': (140, '9bac88f92f4b9e3e384d3530d79bacb9591b78c3a4cd63ee8d1921ddfd333352'),
    '.tar.gz': (10130, ARCHIVE_SHA),
    '.tar.gz.sha256': (125, '8dcf480b9b3642e3318229077d2828f2a8bc36ef0dd86796a4c612a13fcc6b05'),
}
PROJECT = Path('/home/jovyan/adapointr_work/PoinTr')
CODE = PROJECT / 'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
NEW_DIR = CODE / 'evidence/monitor_diagnostic_v3'
REUSE = [
    dict(path=str(CODE / 'bcsp_training_contract_v2.py'), bytes=16538,
         sha256='88b0098ec199fcba7e37c9ca2be7a8d6b69ff246ab0f1b9494445e4a72b41db3'),
    dict(path=str(CODE / 'bcsp_training_runtime_v5.py'), bytes=10171,
         sha256='55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847'),
]
START = time.monotonic()
created, created_dirs = [], []
phase = 'IDENTITY'


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def event(value):
    print(json.dumps(value, ensure_ascii=True), flush=True)


def budget():
    need(time.monotonic() - START < 100, 'installation time budget')


def parents(path, allow_missing=False):
    for p in reversed(path.parents):
        if allow_missing and not os.path.lexists(p):
            need(p == NEW_DIR, 'unlisted missing parent: ' + str(p))
            continue
        need(stat.S_ISDIR(p.lstat().st_mode), 'linked/non-directory parent: ' + str(p))


def absent(path, allow_missing=False):
    parents(path, allow_missing)
    need(not os.path.lexists(path), 'installation collision: ' + str(path))


def read_exact(record):
    budget()
    p = Path(record['path'])
    parents(p)
    st = p.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size == record['bytes'], 'file type/size: ' + str(p))
    raw = p.read_bytes()
    after = p.stat()
    need((st.st_size, st.st_mtime_ns, st.st_ino) ==
         (after.st_size, after.st_mtime_ns, after.st_ino), 'file changed: ' + str(p))
    need(len(raw) == record['bytes'] and sha(raw) == record['sha256'], 'file hash: ' + str(p))
    return raw


def dirfd(path):
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


try:
    need(socket.gethostname() == 'shu-common-25721452-notebook-3x9rq5-0' and os.getuid() == 1000,
         'hostname/uid mismatch')
    parents(PROJECT)
    need(stat.S_ISDIR(PROJECT.lstat().st_mode), 'project path')
    os.chdir(PROJECT)
    need(str(Path.cwd()) == str(PROJECT), 'project cwd')
    gpu = subprocess.run(['/usr/bin/nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total',
                          '--format=csv,noheader,nounits'], stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=10, check=True)
    gpu_header = [x.strip() for x in gpu.stdout.decode('utf-8').strip().split(',')]
    need(gpu_header == ['GPU-4b19574a-832d-b4fe-e655-a57462954d6a',
                        'NVIDIA GeForce RTX 4090 D', '570.190', '24564'], 'GPU binding mismatch')
    phase = 'UPLOADS_AND_ARCHIVE'
    raw_uploads, upload_rows = {}, []
    for suffix, (size, digest) in UPLOAD_EXPECTED.items():
        p = Path('/home/jovyan') / (NAME + suffix)
        row = dict(path=str(p), bytes=size, sha256=digest)
        raw_uploads[suffix] = read_exact(row)
        upload_rows.append(row)
    mapping = json.loads(raw_uploads['.installation_map.json'])
    need(mapping['installation_authorized'] is False and mapping['is_execution_request'] is False,
         'immutable pending mapping')
    rows = mapping['installation_map']
    need(len(rows) == len({r['archive_member'] for r in rows}) ==
         len({r['server_target'] for r in rows}) == 7, 'exact seven mapped files')
    need(mapping['code_root'] == str(CODE) and mapping['explicit_new_evidence_directory'] == str(NEW_DIR),
         'frozen installation roots')
    need(mapping['reuse_readonly_not_repackaged'] == REUSE, 'exact existing prerequisites')
    content = {}
    expected = {r['archive_member']: r for r in rows}
    with tarfile.open(fileobj=io.BytesIO(raw_uploads['.tar.gz']), mode='r:gz') as tar:
        members = tar.getmembers()
        need(len(members) == len({m.name for m in members}) == 7 and
             {m.name for m in members} == set(expected), 'exact archive member set')
        for member in members:
            budget()
            rel = PurePosixPath(member.name)
            need(member.isfile() and not member.issym() and not member.islnk()
                 and member.mode == 0o644 and not rel.is_absolute()
                 and '..' not in rel.parts and '\\' not in member.name, 'member path/type')
            r = expected[member.name]
            need(member.size == r['bytes'] and 0 <= member.size <= 65536, 'member size')
            raw = tar.extractfile(member).read()
            need(len(raw) == r['bytes'] and sha(raw) == r['sha256'], 'member content')
            need(member.name.startswith('code/'), 'only code overlay members')
            target = Path(r['server_target'])
            need(target == CODE / member.name[5:] and
                 (target == CODE / 'bcsp_training_entry_v3.py' or target.parent == NEW_DIR),
                 'exact target boundary')
            need(r['mode'] == 'create_only_no_overwrite', 'no-overwrite mapping')
            content[target] = raw
    need(sum(len(v) for v in content.values()) == 39036, 'exact uncompressed bytes')
    manifest = ''.join(r['sha256'] + '  ' + r['archive_member'] + '\n'
                       for r in sorted(rows, key=lambda x: x['archive_member'])).encode('ascii')
    need(raw_uploads['.contents.sha256'] == manifest and int(raw_uploads['.bytes']) == 10130,
         'manifest and byte sidecars')
    phase = 'ALL_PREWRITE_CHECKS'
    for r in REUSE:
        read_exact(r)
    absent(NEW_DIR)
    need(os.access(NEW_DIR.parent, os.W_OK | os.X_OK) and
         os.access(CODE, os.W_OK | os.X_OK), 'parent write/search permission')
    for target in content:
        absent(target, allow_missing=True)
    free_before = shutil.disk_usage(PROJECT).free
    need(free_before >= 4294967296 + 39036, 'disk reserve plus exact new files')
    # Recheck all absent targets immediately before the first write.
    absent(NEW_DIR)
    for target in content:
        absent(target, allow_missing=True)
    event(dict(status='MONITOR_V3_PREWRITE_CHECKS_PASS', mapping_sha256=MAP_SHA,
               absent_targets=7, absent_new_directory=True, uploads_verified=7,
               archive_members=7, reused_prerequisites=REUSE,
               gpu_identity_query_only=gpu_header, free_bytes=free_before, server_writes_so_far=0))
    phase = 'EXCLUSIVE_INSTALLATION'
    pfd = dirfd(NEW_DIR.parent)
    try:
        os.mkdir(NEW_DIR.name, 0o700, dir_fd=pfd)
        created_dirs.append(str(NEW_DIR))
    finally:
        os.close(pfd)
    for r in rows:
        budget()
        target = Path(r['server_target'])
        absent(target)
        pfd = dirfd(target.parent)
        try:
            fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o644, dir_fd=pfd)
            created.append(str(target))
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o644)
                stream.write(content[target])
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(pfd)
        read_exact(dict(path=str(target), bytes=r['bytes'], sha256=r['sha256']))
    phase = 'FINAL_READBACK'
    for r in rows:
        read_exact(dict(path=r['server_target'], bytes=r['bytes'], sha256=r['sha256']))
    for r in REUSE:
        read_exact(r)
    need(len(created) == 7 and created_dirs == [str(NEW_DIR)], 'installation count')
    event(dict(status='MONITOR_V3_EXCLUSIVE_INSTALL_PASS', mapping_sha256=MAP_SHA,
               installed_files=rows, readback_hash_matches=7, created_directories=created_dirs,
               prerequisites_still_match=REUSE, uploaded_files=upload_rows,
               gpu_identity_query_only=gpu_header, free_bytes_after=shutil.disk_usage(PROJECT).free,
               server_files_created=7, overwrites=0, deletions=0, packaged_code_executed=False,
               tests=0, GPU_compute=0, training_steps=0,
               old_failed_run_modified=False, seconds=time.monotonic()-START,
               UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except BaseException as exc:
    event(dict(status='FAILED_STOP_NO_RETRY', phase=phase, error=repr(exc),
               created_files=created, created_directories=created_dirs,
               preserve_partial_files=True, no_retry=True, no_cleanup=True))
    raise
