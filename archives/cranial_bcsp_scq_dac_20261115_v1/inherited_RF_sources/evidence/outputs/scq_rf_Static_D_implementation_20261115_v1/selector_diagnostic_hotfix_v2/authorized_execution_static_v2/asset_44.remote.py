from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/misc.py', 'bytes': 12290, 'sha256': '3063afb490840dd417c2e0cc00f2d5fdfe49ba2074396099c39a112026906485'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/pointnet2_utils.py', 'bytes': 4275, 'sha256': '6e814a64b244d018047ffefa92004dd4e59fc941145476af1424aae1742c43ec'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d22_geometry.py', 'bytes': 12533, 'sha256': '8b3b56344f7e9c97a3cd1ee141964bc7797faae4f094df9404dedaee07e6c804'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d3_contact.py', 'bytes': 11021, 'sha256': '10c5bb39a8cf3860ed28b65d2c9257ae1ff4e63c4b69228504dd663f0604e5cb'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/misc.py', 'bytes': 12290, 'sha256': '3063afb490840dd417c2e0cc00f2d5fdfe49ba2074396099c39a112026906485'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/pointnet2_utils.py', 'bytes': 4275, 'sha256': '6e814a64b244d018047ffefa92004dd4e59fc941145476af1424aae1742c43ec'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d22_geometry.py', 'bytes': 12533, 'sha256': '8b3b56344f7e9c97a3cd1ee141964bc7797faae4f094df9404dedaee07e6c804'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d3_contact.py', 'bytes': 11021, 'sha256': '10c5bb39a8cf3860ed28b65d2c9257ae1ff4e63c4b69228504dd663f0604e5cb'}]), hashed_bytes=total)))