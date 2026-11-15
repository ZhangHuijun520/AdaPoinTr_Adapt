from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_construction_v3.json', 'bytes': 2181, 'sha256': 'fae4f3d689665c54b4c162d9004480a915592f58e42255d3a8c9f31d5d6650ae'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_completion_v3.json', 'bytes': 293297, 'sha256': '9b2d98509ebb03a59b8dd14d0332f0ba4d176248023a86f3c7d999516969335a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_request_v3.json', 'bytes': 31882, 'sha256': '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/runner.py', 'relative_target': 'tools/runner.py', 'sha256': 'e378ab4ab7a26f6b370b4263788ca51e413b47ca3827cf404dd6ac4d9aaa0f32', 'bytes': 32455}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_construction_v3.json', 'bytes': 2181, 'sha256': 'fae4f3d689665c54b4c162d9004480a915592f58e42255d3a8c9f31d5d6650ae'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_completion_v3.json', 'bytes': 293297, 'sha256': '9b2d98509ebb03a59b8dd14d0332f0ba4d176248023a86f3c7d999516969335a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_request_v3.json', 'bytes': 31882, 'sha256': '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/runner.py', 'relative_target': 'tools/runner.py', 'sha256': 'e378ab4ab7a26f6b370b4263788ca51e413b47ca3827cf404dd6ac4d9aaa0f32', 'bytes': 32455}]), hashed_bytes=total)))