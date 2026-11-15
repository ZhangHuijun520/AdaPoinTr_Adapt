from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm-2.3.1.dist-info/METADATA', 'bytes': 25449, 'sha256': 'de580cd29b3bf2c8d81240fad9255978be1835884b82ab8e84f17f4ba720effd'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d-1.6.2.post1.dist-info/METADATA', 'bytes': 1625, 'sha256': '3b4a001f4ad6f856465746601e4b0dda9b2d088bd8e81b6376e4a707fcf4ca7b'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/selective_scan_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 526135264, 'sha256': '5e6a5bfabe7628720631568ec364426e6066da9a9a0946302ebe9fb86f4aa58c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 166702752, 'sha256': '6ac9c334498773ee337503094d7b5aae4b0f38fa3ba8a0dcd81cca707f48a79a'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm-2.3.1.dist-info/METADATA', 'bytes': 25449, 'sha256': 'de580cd29b3bf2c8d81240fad9255978be1835884b82ab8e84f17f4ba720effd'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d-1.6.2.post1.dist-info/METADATA', 'bytes': 1625, 'sha256': '3b4a001f4ad6f856465746601e4b0dda9b2d088bd8e81b6376e4a707fcf4ca7b'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/selective_scan_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 526135264, 'sha256': '5e6a5bfabe7628720631568ec364426e6066da9a9a0946302ebe9fb86f4aa58c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 166702752, 'sha256': '6ac9c334498773ee337503094d7b5aae4b0f38fa3ba8a0dcd81cca707f48a79a'}]), hashed_bytes=total)))