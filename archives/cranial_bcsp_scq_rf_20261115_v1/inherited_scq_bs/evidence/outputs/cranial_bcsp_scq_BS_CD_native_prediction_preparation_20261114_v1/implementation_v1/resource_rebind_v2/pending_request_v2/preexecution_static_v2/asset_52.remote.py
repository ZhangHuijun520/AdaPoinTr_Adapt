from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/_ext.cpython-310-x86_64-linux-gnu.so', 'exists': True, 'bytes': 301640, 'sha256': 'e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/wheelhouse/pointnet2_ops-3.0.0-cp310-cp310-linux_x86_64.whl', 'exists': True, 'bytes': 123291, 'sha256': '530496a0d1d5dea6151a466b7c0874632322223308a7016910fb1bfbaaaab1e5'}, {'path': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'exists': True, 'bytes': 17331920, 'sha256': '01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/base_model.yaml', 'sha256': 'e18feb90d782506f864560ce5513b3077f840f9d6365308b03493f80f8c57dc4', 'bytes': 2082}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/_ext.cpython-310-x86_64-linux-gnu.so', 'exists': True, 'bytes': 301640, 'sha256': 'e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/wheelhouse/pointnet2_ops-3.0.0-cp310-cp310-linux_x86_64.whl', 'exists': True, 'bytes': 123291, 'sha256': '530496a0d1d5dea6151a466b7c0874632322223308a7016910fb1bfbaaaab1e5'}, {'path': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'exists': True, 'bytes': 17331920, 'sha256': '01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/base_model.yaml', 'sha256': 'e18feb90d782506f864560ce5513b3077f840f9d6365308b03493f80f8c57dc4', 'bytes': 2082}]), hashed_bytes=total)))