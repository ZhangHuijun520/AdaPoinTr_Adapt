from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}]), hashed_bytes=total)))