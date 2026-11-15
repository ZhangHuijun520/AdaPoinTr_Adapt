from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json', 'bytes': 23220, 'sha256': 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/AdaPoinTr.py', 'bytes': 103347, 'sha256': '1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json', 'bytes': 23220, 'sha256': 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/AdaPoinTr.py', 'bytes': 103347, 'sha256': '1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'}]), hashed_bytes=total)))