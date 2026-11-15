from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/__init__.py', 'bytes': 264, 'sha256': '6d3fee6ff8e8ec4dcab0f7af6c7890ff81f3d9319707865f5a651239aee9ae0a'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/modules/mamba_simple.py', 'bytes': 11710, 'sha256': 'a17e4c51b582dc0d4d690a649eba521cd0c1ee3dc8f0473a0967cdc9ec0874e3'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/ops/selective_scan_interface.py', 'bytes': 20025, 'sha256': '543edd077f11c80cccd5c5e2f926420d9105fd238d9e8960e53660cfa234dce8'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/__init__.py', 'bytes': 264, 'sha256': '6d3fee6ff8e8ec4dcab0f7af6c7890ff81f3d9319707865f5a651239aee9ae0a'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/modules/mamba_simple.py', 'bytes': 11710, 'sha256': 'a17e4c51b582dc0d4d690a649eba521cd0c1ee3dc8f0473a0967cdc9ec0874e3'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/ops/selective_scan_interface.py', 'bytes': 20025, 'sha256': '543edd077f11c80cccd5c5e2f926420d9105fd238d9e8960e53660cfa234dce8'}]), hashed_bytes=total)))