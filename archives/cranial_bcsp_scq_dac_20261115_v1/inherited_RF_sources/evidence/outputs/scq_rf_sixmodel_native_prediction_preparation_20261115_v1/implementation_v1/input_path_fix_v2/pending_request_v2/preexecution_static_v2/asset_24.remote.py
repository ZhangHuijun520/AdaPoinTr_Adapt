from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch-2.4.1+cu118.dist-info/METADATA', 'exists': True, 'bytes': 26707, 'sha256': '11606497a9792f0d040ad062064ee1c024dde8b10fc38bed361134d0b7ec429a', 'name_version': ['Name: torch', 'Version: 2.4.1+cu118']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'exists': True, 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4', 'name_version': ['Name: timm', 'Version: 1.0.27']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'exists': True, 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a', 'name_version': ['Name: numpy', 'Version: 2.2.6']}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch-2.4.1+cu118.dist-info/METADATA', 'exists': True, 'bytes': 26707, 'sha256': '11606497a9792f0d040ad062064ee1c024dde8b10fc38bed361134d0b7ec429a', 'name_version': ['Name: torch', 'Version: 2.4.1+cu118']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'exists': True, 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4', 'name_version': ['Name: timm', 'Version: 1.0.27']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'exists': True, 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a', 'name_version': ['Name: numpy', 'Version: 2.2.6']}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}]), hashed_bytes=total)))