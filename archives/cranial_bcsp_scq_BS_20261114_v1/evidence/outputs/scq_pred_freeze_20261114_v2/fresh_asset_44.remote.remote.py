from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/logger.py', 'relative_path': 'utils/logger.py', 'sha256': '12e50962ca4594ddd573d9a76524ac912ddf55bfc297fa8008a30b20dca28e0c', 'bytes': 5048}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/misc.py', 'relative_path': 'utils/misc.py', 'sha256': '3063afb490840dd417c2e0cc00f2d5fdfe49ba2074396099c39a112026906485', 'bytes': 12290}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/pointnet2_utils.py', 'relative_path': 'utils/pointnet2_utils.py', 'sha256': '6e814a64b244d018047ffefa92004dd4e59fc941145476af1424aae1742c43ec', 'bytes': 4275}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d22_geometry.py', 'relative_path': 'utils/mamba_d22_geometry.py', 'sha256': '8b3b56344f7e9c97a3cd1ee141964bc7797faae4f094df9404dedaee07e6c804', 'bytes': 12533}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/logger.py', 'relative_path': 'utils/logger.py', 'sha256': '12e50962ca4594ddd573d9a76524ac912ddf55bfc297fa8008a30b20dca28e0c', 'bytes': 5048}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/misc.py', 'relative_path': 'utils/misc.py', 'sha256': '3063afb490840dd417c2e0cc00f2d5fdfe49ba2074396099c39a112026906485', 'bytes': 12290}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/pointnet2_utils.py', 'relative_path': 'utils/pointnet2_utils.py', 'sha256': '6e814a64b244d018047ffefa92004dd4e59fc941145476af1424aae1742c43ec', 'bytes': 4275}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/utils/mamba_d22_geometry.py', 'relative_path': 'utils/mamba_d22_geometry.py', 'sha256': '8b3b56344f7e9c97a3cd1ee141964bc7797faae4f094df9404dedaee07e6c804', 'bytes': 12533}]), hashed_bytes=total)))