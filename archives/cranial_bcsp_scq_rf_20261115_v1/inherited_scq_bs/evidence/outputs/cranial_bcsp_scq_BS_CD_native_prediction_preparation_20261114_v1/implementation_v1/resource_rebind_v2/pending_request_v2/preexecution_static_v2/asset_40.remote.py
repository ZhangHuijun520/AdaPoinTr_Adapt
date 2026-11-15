from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/local_geometry.py', 'relative_path': 'models/cranial_scqr/local_geometry.py', 'sha256': 'e3e2eb20aed6afb3024f8b3c10c79ac0f64f288f3892495668980028793ba768', 'bytes': 6413}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'relative_path': 'models/cranial_scqr/query_conditioning.py', 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942', 'bytes': 4719}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'relative_path': 'utils/registry.py', 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7', 'bytes': 11111}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'relative_path': 'utils/config.py', 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819', 'bytes': 2438}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/local_geometry.py', 'relative_path': 'models/cranial_scqr/local_geometry.py', 'sha256': 'e3e2eb20aed6afb3024f8b3c10c79ac0f64f288f3892495668980028793ba768', 'bytes': 6413}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'relative_path': 'models/cranial_scqr/query_conditioning.py', 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942', 'bytes': 4719}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'relative_path': 'utils/registry.py', 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7', 'bytes': 11111}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'relative_path': 'utils/config.py', 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819', 'bytes': 2438}]), hashed_bytes=total)))