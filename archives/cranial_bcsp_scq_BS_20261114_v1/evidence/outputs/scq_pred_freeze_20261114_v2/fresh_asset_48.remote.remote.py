from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d3_contact.py', 'relative_path': 'utils/mamba_d3_contact.py', 'sha256': '10c5bb39a8cf3860ed28b65d2c9257ae1ff4e63c4b69228504dd663f0604e5cb', 'bytes': 11021}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/extensions/chamfer_dist/__init__.py', 'relative_path': 'extensions/chamfer_dist/__init__.py', 'sha256': '6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50', 'bytes': 6551}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'exists': True, 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'exists': True, 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d3_contact.py', 'relative_path': 'utils/mamba_d3_contact.py', 'sha256': '10c5bb39a8cf3860ed28b65d2c9257ae1ff4e63c4b69228504dd663f0604e5cb', 'bytes': 11021}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/extensions/chamfer_dist/__init__.py', 'relative_path': 'extensions/chamfer_dist/__init__.py', 'sha256': '6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50', 'bytes': 6551}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/__init__.py', 'exists': True, 'bytes': 123, 'sha256': 'd8a0921aeb90349a0659799a22ccf00ccd31707b226426ff4118eeb65ae0ada2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/provider/pointnet2_ops/pointnet2_utils.py', 'exists': True, 'bytes': 9943, 'sha256': 'ec597d77b1215fbc87bdb452b8ce04b85eb0b816d5e39e7696fc792a2f61ea5b'}]), hashed_bytes=total)))