from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch/version.py', 'exists': True, 'bytes': 248, 'sha256': 'b10649fd636e7404398d608b84a2cacc6645e3952f043b439d4c50c95a26a1b5', 'assignments': {'__version__': '2.4.1+cu118', 'debug': False, 'git_version': '38b96d3399a695e704ed39b60dac733c3fbf20e2'}}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch-2.4.1+cu118.dist-info/METADATA', 'exists': True, 'bytes': 26707, 'sha256': '11606497a9792f0d040ad062064ee1c024dde8b10fc38bed361134d0b7ec429a', 'name_version': ['Name: torch', 'Version: 2.4.1+cu118']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'exists': True, 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4', 'name_version': ['Name: timm', 'Version: 1.0.27']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'exists': True, 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a', 'name_version': ['Name: numpy', 'Version: 2.2.6']}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch/version.py', 'exists': True, 'bytes': 248, 'sha256': 'b10649fd636e7404398d608b84a2cacc6645e3952f043b439d4c50c95a26a1b5', 'assignments': {'__version__': '2.4.1+cu118', 'debug': False, 'git_version': '38b96d3399a695e704ed39b60dac733c3fbf20e2'}}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch-2.4.1+cu118.dist-info/METADATA', 'exists': True, 'bytes': 26707, 'sha256': '11606497a9792f0d040ad062064ee1c024dde8b10fc38bed361134d0b7ec429a', 'name_version': ['Name: torch', 'Version: 2.4.1+cu118']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'exists': True, 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4', 'name_version': ['Name: timm', 'Version: 1.0.27']}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'exists': True, 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a', 'name_version': ['Name: numpy', 'Version: 2.2.6']}]), hashed_bytes=total)))