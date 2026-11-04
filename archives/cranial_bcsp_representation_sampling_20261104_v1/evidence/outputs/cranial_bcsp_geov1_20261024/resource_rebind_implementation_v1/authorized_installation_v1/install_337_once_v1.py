"""Single authorized exclusive installation; never import or run packaged code."""
import datetime, hashlib, io, json, os, shutil, socket, stat, subprocess, sys, tarfile, time
from pathlib import Path, PurePosixPath
SCOPE_SHA = '42d0b302e40ec0d127c147063b0df9ddd662aa1ef37d964387dd3c8081cd6e62'
MAP_SHA = 'fa12562dd065c8d4a1016d7ec5550f3f1b30fb4e97148b262b6090631c1e43b1'
UPLOADS = [
  {
    "filename": "bcsp_foldc_8192_train_inputs_v1.bytes",
    "server_path": "/home/jovyan/bcsp_foldc_8192_train_inputs_v1.bytes",
    "bytes": 9,
    "sha256": "30a5e7adafb7d01c0539acac4bb50072a8b36e9a275feb7171d19a67a2c35675"
  },
  {
    "filename": "bcsp_foldc_8192_train_inputs_v1.contents.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_train_inputs_v1.contents.sha256",
    "bytes": 36108,
    "sha256": "1d5f43673c76b93d3195aad25e19de4a229fdc2c23505395d993c548175b823e"
  },
  {
    "filename": "bcsp_foldc_8192_train_inputs_v1.contents.sha256.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_train_inputs_v1.contents.sha256.sha256",
    "bytes": 114,
    "sha256": "993be616ec45dd2146441b7c2de31063a6df97e41232def645df3e3d5b4be7ae"
  },
  {
    "filename": "bcsp_foldc_8192_train_inputs_v1.tar.gz",
    "server_path": "/home/jovyan/bcsp_foldc_8192_train_inputs_v1.tar.gz",
    "bytes": 49773476,
    "sha256": "fc3c4daa64f7a90ff6396d039c43344ab4d07947d12b675c1ecd4d6c54a08c0d"
  },
  {
    "filename": "bcsp_foldc_8192_train_inputs_v1.tar.gz.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_train_inputs_v1.tar.gz.sha256",
    "bytes": 105,
    "sha256": "66d75f0c2b1f33966cb71f07a2ef2d942508025b2a5bcfd6c5be0483557f7e71"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.bytes",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.bytes",
    "bytes": 6,
    "sha256": "ac5b917e579e7d4fddd2696290e92e3448c55e87ee57889e61ae27da9f51257d"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.contents.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.contents.sha256",
    "bytes": 1157,
    "sha256": "2521bcefb4b51717e374a8fcfa1d5be9c4e883f4ab97500766df9a169731e4ce"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.contents.sha256.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.contents.sha256.sha256",
    "bytes": 128,
    "sha256": "d0d6361c6070702c2d732593a42c7689dc07feb96a0f8fcace9ef3dc60893523"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.installation_map.json",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.installation_map.json",
    "bytes": 13259,
    "sha256": "93d5ca2e34ddf39a5ecc40e53d8610b1c05d35ba1ead5082f28947f6119f6332"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.installation_map.json.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.installation_map.json.sha256",
    "bytes": 134,
    "sha256": "f6d338935e8018667278467438f5960c37127a990bedcb3f9dd9ba29bd6da093"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.tar.gz",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.tar.gz",
    "bytes": 21984,
    "sha256": "278e2678c5af9da2fd18b08cbf27b73ee6f2e48c4dbc42f0382a907417893987"
  },
  {
    "filename": "bcsp_foldc_8192_resource_rebind_supplement_v1.tar.gz.sha256",
    "server_path": "/home/jovyan/bcsp_foldc_8192_resource_rebind_supplement_v1.tar.gz.sha256",
    "bytes": 119,
    "sha256": "7d080e0f3e9f62391cfaef77402f07263a6f4ab4a895b0cde238d7df7ebdcad5"
  }
]
NEW_DIRS = [
  "/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1",
  "/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1",
  "/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points",
  "/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence",
  "/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/resource_rebind_v1"
]
PROJECT = Path('/home/jovyan/adapointr_work/PoinTr')
CODE = PROJECT / 'third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
DATA = PROJECT / 'data/bcsp_geov1_foldc_8192_seed0_v1'
START = time.monotonic()
created, created_dirs, checked_uploads = [], [], []
phase = 'IDENTITY'
def require(ok, why):
    if not ok:
        raise RuntimeError(why)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def budget():
    require(time.monotonic() - START < 115, 'cooperative installation timeout')
def event(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)
def parents(path):
    for p in reversed(path.parents):
        if os.path.lexists(p):
            require(stat.S_ISDIR(p.lstat().st_mode), 'non-directory/link ancestor: ' + str(p))
def absent(path):
    parents(path)
    require(not os.path.lexists(path), 'target collision: ' + str(path))
def secure_dir(path):
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
def readback(path, expected):
    parents(path)
    pfd = secure_dir(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=pfd)
        with os.fdopen(fd, 'rb') as stream:
            st = os.fstat(stream.fileno())
            require(stat.S_ISREG(st.st_mode) and st.st_size == expected['bytes'],
                    'readback type/size: ' + str(path))
            raw = stream.read(expected['bytes'] + 1)
        require(len(raw) == expected['bytes'] and sha(raw) == expected['sha256'],
                'readback hash: ' + str(path))
    finally:
        os.close(pfd)
try:
    require(socket.gethostname() == 'shu-common-25721452-notebook-3x9rq5-0' and os.getuid() == 1000,
            'container/uid identity')
    parents(PROJECT)
    require(stat.S_ISDIR(PROJECT.lstat().st_mode), 'project directory')
    os.chdir(PROJECT)
    require(str(Path.cwd()) == str(PROJECT), 'project cwd')
    smi = subprocess.run(['/usr/bin/nvidia-smi', '--query-gpu=uuid,name,driver_version,memory.total',
                          '--format=csv,noheader,nounits'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         timeout=10, check=True)
    gpu = [x.strip() for x in smi.stdout.decode('utf-8').strip().split(',')]
    require(gpu == ['GPU-4b19574a-832d-b4fe-e655-a57462954d6a', 'NVIDIA GeForce RTX 4090 D',
                    '570.190', '24564'], 'fixed resource-rebind GPU identity')
    phase = 'UPLOADS'
    uploads = {}
    for row in UPLOADS:
        budget()
        p = Path(row['server_path'])
        parents(p)
        st = p.lstat()
        require(stat.S_ISREG(st.st_mode) and st.st_size == row['bytes'], 'upload type/size: ' + str(p))
        raw = p.read_bytes()
        after = p.stat()
        require((st.st_size, st.st_mtime_ns, st.st_ino) ==
                (after.st_size, after.st_mtime_ns, after.st_ino), 'upload changed: ' + str(p))
        require(sha(raw) == row['sha256'], 'upload hash: ' + str(p))
        uploads[row['filename']] = raw
        checked_uploads.append(dict(filename=row['filename'], bytes=len(raw), sha256=sha(raw)))
    require(len(uploads) == 12, 'exact twelve uploads')
    phase = 'ARCHIVES'
    n1, n2 = 'bcsp_foldc_8192_train_inputs_v1', 'bcsp_foldc_8192_resource_rebind_supplement_v1'
    manifest = dict((name, digest) for digest, name in
                    (line.split('  ', 1) for line in uploads[n1 + '.contents.sha256'].decode('ascii').splitlines()))
    require(len(manifest) == 327, 'original exact manifest')
    supplement = json.loads(uploads[n2 + '.installation_map.json'])
    second = dict((r['archive_member'], r) for r in supplement['installation_map'])
    require(len(second) == 10, 'supplement exact map')
    files, contents = [], {}
    for phase_number, n in [(1, n1), (2, n2)]:
        expected = manifest if phase_number == 1 else second
        seen = set()
        with tarfile.open(fileobj=io.BytesIO(uploads[n + '.tar.gz']), mode='r:gz') as tar:
            members = tar.getmembers()
            require(len(members) == len(expected), 'archive member count: ' + n)
            for m in members:
                budget()
                rel = PurePosixPath(m.name)
                require(m.isfile() and not m.issym() and not m.islnk() and m.mode == 0o644,
                        'archive member type/mode: ' + m.name)
                require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in m.name
                        and m.name not in seen and m.name in expected, 'archive path/set: ' + m.name)
                require(0 <= m.size <= 4194304, 'member size ceiling')
                seen.add(m.name)
                raw = tar.extractfile(m).read()
                require(len(raw) == m.size, 'member byte count')
                digest = sha(raw)
                if phase_number == 1:
                    require(digest == manifest[m.name] and m.size > 0, 'original member hash')
                    require(m.name.startswith('code/') or m.name.startswith('data/'), 'original prefix')
                    target = (CODE if m.name.startswith('code/') else DATA) / m.name[5:]
                else:
                    r = second[m.name]
                    require(digest == r['sha256'] and m.size == r['bytes'], 'supplement member hash')
                    target = Path(r['server_target'])
                    require(m.name.startswith('code/') and target == CODE / m.name[5:],
                            'supplement target mapping')
                require(target not in contents and (CODE in target.parents or DATA in target.parents),
                        'target boundary/duplicate')
                row = dict(archive_member=m.name, server_target=str(target), bytes=len(raw), sha256=digest)
                files.append(row)
                contents[target] = (phase_number, raw, row)
            require(seen == set(expected), 'archive exact set')
    require(len(files) == 337 and sum(r['bytes'] for r in files) == 51774293, 'total frozen files/bytes')
    canonical = json.dumps(sorted(files, key=lambda r: r['server_target']), sort_keys=True,
                           separators=(',', ':')).encode()
    require(sha(canonical) == MAP_SHA, 'exact337 mapping differs from authorized scope')
    phase = 'ALL_TARGETS_BEFORE_WRITES'
    for p in contents:
        absent(p)
    needed = set()
    for p in contents:
        for a in p.parents:
            if not os.path.lexists(a):
                needed.add(str(a))
    require(needed == set(NEW_DIRS), 'new parent directory range changed')
    for value in NEW_DIRS:
        absent(Path(value))
    require(all(os.access(p, os.W_OK | os.X_OK) for p in (CODE.parent, DATA.parent)),
            'existing parent write/search permission')
    free_before = shutil.disk_usage(PROJECT).free
    require(free_before >= 4294967296 + 51774293, 'minimum disk reserve plus exact new files')
    event(dict(status='ALL_PREWRITE_CHECKS_PASS', scope_sha256=SCOPE_SHA, uploads=12,
               original_members=327, supplement_members=10, absent_targets=337,
               directory_creations=len(NEW_DIRS), GPU_identity=gpu, free_bytes=free_before,
               server_writes_so_far=0))
    phase = 'CREATE_DIRS'
    for value in NEW_DIRS:
        budget()
        p = Path(value)
        absent(p)
        pfd = secure_dir(p.parent)
        try:
            os.mkdir(p.name, 0o700, dir_fd=pfd)
            created_dirs.append(str(p))
        finally:
            os.close(pfd)
    phase = 'EXCLUSIVE_INSTALL'
    ordered = sorted(contents.items(), key=lambda item: (item[1][0], str(item[0])))
    for p, (number, raw, row) in ordered:
        budget()
        absent(p)
        require(shutil.disk_usage(PROJECT).free >= 4294967296 + len(raw), 'disk stopping reserve')
        pfd = secure_dir(p.parent)
        try:
            fd = os.open(p.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o644, dir_fd=pfd)
            created.append(str(p))
            with os.fdopen(fd, 'wb') as stream:
                os.fchmod(stream.fileno(), 0o644)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            os.close(pfd)
        readback(p, row)
    phase = 'FINAL_READBACK'
    for p, (_, _, row) in ordered:
        budget()
        readback(p, row)
    require(len(created) == 337, 'installed count')
    event(dict(status='EXCLUSIVE_INSTALL_337_PASS', scope_sha256=SCOPE_SHA,
               canonical_map_sha256=MAP_SHA, installed_files=files, created_directories=created_dirs,
               uploaded_files=checked_uploads, total_file_bytes=51774293,
               readback_hash_matches=337, GPU_identity_query_only=gpu, new_gpu_execution_validated=False,
               packaged_code_executed=False, tests=0, forwards=0, training_steps=0,
               overwrites=0, deletions=0, free_bytes_after=shutil.disk_usage(PROJECT).free,
               seconds=time.monotonic()-START, UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
except BaseException as exc:
    event(dict(status='FAILED_STOP_NO_RETRY', phase=phase, error=repr(exc),
               created_files=created, created_directories=created_dirs,
               scope_sha256=SCOPE_SHA, preserve_partial_output=True, no_cleanup=True,
               packaged_code_executed=False))
    raise
