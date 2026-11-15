from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/local_geometry.py', 'bytes': 6413, 'sha256': 'e3e2eb20aed6afb3024f8b3c10c79ac0f64f288f3892495668980028793ba768'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'bytes': 4719, 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'bytes': 11111, 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'bytes': 2438, 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/local_geometry.py', 'bytes': 6413, 'sha256': 'e3e2eb20aed6afb3024f8b3c10c79ac0f64f288f3892495668980028793ba768'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'bytes': 4719, 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'bytes': 11111, 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'bytes': 2438, 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819'}]), hashed_bytes=total)))