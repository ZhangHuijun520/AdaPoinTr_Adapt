from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'bytes': 4719, 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'bytes': 11111, 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'bytes': 2438, 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/logger.py', 'bytes': 5048, 'sha256': '12e50962ca4594ddd573d9a76524ac912ddf55bfc297fa8008a30b20dca28e0c'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/models/cranial_scqr/query_conditioning.py', 'bytes': 4719, 'sha256': '7c09def4ea7f2d65906e7fc3de753cae699be6d2d4ad3dcbb33e231be37a6942'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/registry.py', 'bytes': 11111, 'sha256': 'a7c49418d587ae84778390b67a50c2bd98cbc93da2e0a506e6d309b5c159ecf7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/config.py', 'bytes': 2438, 'sha256': '39d487ab6eadcd0a157167cfdf0d1797255f6403828f2653ba7802da6f2ac819'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/logger.py', 'bytes': 5048, 'sha256': '12e50962ca4594ddd573d9a76524ac912ddf55bfc297fa8008a30b20dca28e0c'}]), hashed_bytes=total)))