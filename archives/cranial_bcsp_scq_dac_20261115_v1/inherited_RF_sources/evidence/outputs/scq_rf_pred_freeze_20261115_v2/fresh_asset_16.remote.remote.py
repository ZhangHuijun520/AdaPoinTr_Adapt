from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/ops/selective_scan_interface.py', 'bytes': 20025, 'sha256': '543edd077f11c80cccd5c5e2f926420d9105fd238d9e8960e53660cfa234dce8'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d/__init__.py', 'bytes': 118, 'sha256': 'af95401837aff56ae3749c2237eaff7df8c6a4328d7c5cc6a6731287ac27152c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d/causal_conv1d_interface.py', 'bytes': 8850, 'sha256': '221f41aa963a8f84683d9c6b2b4bf448692feb963fefcd778fa1b4ed2688c859'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm-2.3.1.dist-info/METADATA', 'bytes': 25449, 'sha256': 'de580cd29b3bf2c8d81240fad9255978be1835884b82ab8e84f17f4ba720effd'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/ops/selective_scan_interface.py', 'bytes': 20025, 'sha256': '543edd077f11c80cccd5c5e2f926420d9105fd238d9e8960e53660cfa234dce8'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d/__init__.py', 'bytes': 118, 'sha256': 'af95401837aff56ae3749c2237eaff7df8c6a4328d7c5cc6a6731287ac27152c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d/causal_conv1d_interface.py', 'bytes': 8850, 'sha256': '221f41aa963a8f84683d9c6b2b4bf448692feb963fefcd778fa1b4ed2688c859'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm-2.3.1.dist-info/METADATA', 'bytes': 25449, 'sha256': 'de580cd29b3bf2c8d81240fad9255978be1835884b82ab8e84f17f4ba720effd'}]), hashed_bytes=total)))