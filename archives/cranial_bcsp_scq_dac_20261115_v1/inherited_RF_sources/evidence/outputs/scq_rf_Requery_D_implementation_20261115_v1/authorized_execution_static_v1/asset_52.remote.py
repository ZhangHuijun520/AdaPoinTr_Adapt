from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_adapter.py', 'bytes': 7297, 'sha256': '2f7d3050cfb6ac2602cc17a95b860da2204daef2dfa63dab63d233e899b7dd55'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/_ext.cpython-310-x86_64-linux-gnu.so', 'bytes': 301640, 'sha256': 'e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_adapter.py', 'bytes': 7297, 'sha256': '2f7d3050cfb6ac2602cc17a95b860da2204daef2dfa63dab63d233e899b7dd55'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/_ext.cpython-310-x86_64-linux-gnu.so', 'bytes': 301640, 'sha256': 'e70d00108bacba4a905dc011f4b8c4868f06ec2d44d8e322148e2e452578fbb5'}]), hashed_bytes=total)))