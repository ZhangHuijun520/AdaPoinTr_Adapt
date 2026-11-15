from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d-1.6.2.post1.dist-info/METADATA', 'bytes': 1625, 'sha256': '3b4a001f4ad6f856465746601e4b0dda9b2d088bd8e81b6376e4a707fcf4ca7b'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/selective_scan_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 526135264, 'sha256': '5e6a5bfabe7628720631568ec364426e6066da9a9a0946302ebe9fb86f4aa58c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 166702752, 'sha256': '6ac9c334498773ee337503094d7b5aae4b0f38fa3ba8a0dcd81cca707f48a79a'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch/version.py', 'exists': True, 'bytes': 248, 'sha256': 'b10649fd636e7404398d608b84a2cacc6645e3952f043b439d4c50c95a26a1b5', 'assignments': {'__version__': '2.4.1+cu118', 'debug': False, 'git_version': '38b96d3399a695e704ed39b60dac733c3fbf20e2'}}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d-1.6.2.post1.dist-info/METADATA', 'bytes': 1625, 'sha256': '3b4a001f4ad6f856465746601e4b0dda9b2d088bd8e81b6376e4a707fcf4ca7b'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/selective_scan_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 526135264, 'sha256': '5e6a5bfabe7628720631568ec364426e6066da9a9a0946302ebe9fb86f4aa58c'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/causal_conv1d_cuda.cpython-310-x86_64-linux-gnu.so', 'bytes': 166702752, 'sha256': '6ac9c334498773ee337503094d7b5aae4b0f38fa3ba8a0dcd81cca707f48a79a'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/torch/version.py', 'exists': True, 'bytes': 248, 'sha256': 'b10649fd636e7404398d608b84a2cacc6645e3952f043b439d4c50c95a26a1b5', 'assignments': {'__version__': '2.4.1+cu118', 'debug': False, 'git_version': '38b96d3399a695e704ed39b60dac733c3fbf20e2'}}]), hashed_bytes=total)))