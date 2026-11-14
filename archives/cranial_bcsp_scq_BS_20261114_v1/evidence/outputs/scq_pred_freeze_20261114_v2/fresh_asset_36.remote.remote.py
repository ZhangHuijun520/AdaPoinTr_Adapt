from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/AdaPoinTr.py', 'relative_path': 'models/AdaPoinTr.py', 'sha256': '1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4', 'bytes': 103347}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/build.py', 'relative_path': 'models/build.py', 'sha256': '9c85271220ba992d56d4285b1ef51de939f7471b0712028af8d07880fed9680f', 'bytes': 342}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/__init__.py', 'relative_path': 'models/cranial_scqr/__init__.py', 'sha256': 'c4fab9f4cc19bf5c461930749cccea56cb5b3e7432172d2a4959d2cbc2d69634', 'bytes': 5859}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/contact_support.py', 'relative_path': 'models/cranial_scqr/contact_support.py', 'sha256': '2c92404ba4bd5634a49f396904b2d6f69a22aa2c87bb72f6ee32672ee9d735d1', 'bytes': 6731}]:
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
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/AdaPoinTr.py', 'relative_path': 'models/AdaPoinTr.py', 'sha256': '1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4', 'bytes': 103347}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/build.py', 'relative_path': 'models/build.py', 'sha256': '9c85271220ba992d56d4285b1ef51de939f7471b0712028af8d07880fed9680f', 'bytes': 342}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/__init__.py', 'relative_path': 'models/cranial_scqr/__init__.py', 'sha256': 'c4fab9f4cc19bf5c461930749cccea56cb5b3e7432172d2a4959d2cbc2d69634', 'bytes': 5859}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/contact_support.py', 'relative_path': 'models/cranial_scqr/contact_support.py', 'sha256': '2c92404ba4bd5634a49f396904b2d6f69a22aa2c87bb72f6ee32672ee9d735d1', 'bytes': 6731}]), hashed_bytes=total)))