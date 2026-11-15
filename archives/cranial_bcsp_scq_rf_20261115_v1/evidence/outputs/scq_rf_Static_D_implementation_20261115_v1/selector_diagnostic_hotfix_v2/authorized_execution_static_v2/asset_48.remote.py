from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/extensions/chamfer_dist/__init__.py', 'bytes': 6551, 'sha256': '6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/runner.py', 'bytes': 32455, 'sha256': 'e378ab4ab7a26f6b370b4263788ca51e413b47ca3827cf404dd6ac4d9aaa0f32'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/Transformer_utils.py', 'bytes': 52026, 'sha256': 'cd562e02755ffd46382cc539cdb361225b844b12e89df9d98741d37238a6bf5f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_runtime.py', 'bytes': 7320, 'sha256': '8cbb5389e074347f6bf6e776755d22bbdaedaf5dba5102d51866d1b1e49b3615'}]:
    p = Path(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
    assert p.stat().st_size == r['bytes']
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(4194304), b''):
            h.update(b)
            total += len(b)
    after = p.stat()
    assert (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/extensions/chamfer_dist/__init__.py', 'bytes': 6551, 'sha256': '6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/runner.py', 'bytes': 32455, 'sha256': 'e378ab4ab7a26f6b370b4263788ca51e413b47ca3827cf404dd6ac4d9aaa0f32'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/Transformer_utils.py', 'bytes': 52026, 'sha256': 'cd562e02755ffd46382cc539cdb361225b844b12e89df9d98741d37238a6bf5f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_runtime.py', 'bytes': 7320, 'sha256': '8cbb5389e074347f6bf6e776755d22bbdaedaf5dba5102d51866d1b1e49b3615'}]), hashed_bytes=total)))