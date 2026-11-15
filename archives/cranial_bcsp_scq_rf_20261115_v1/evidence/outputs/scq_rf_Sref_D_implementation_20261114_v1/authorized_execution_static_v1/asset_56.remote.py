from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/wheelhouse/pointnet2_ops-3.0.0-cp310-cp310-linux_x86_64.whl', 'bytes': 123291, 'sha256': '530496a0d1d5dea6151a466b7c0874632322223308a7016910fb1bfbaaaab1e5'}, {'path': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'bytes': 17331920, 'sha256': '01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/base_model.yaml', 'bytes': 2082, 'sha256': 'e18feb90d782506f864560ce5513b3077f840f9d6365308b03493f80f8c57dc4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/r1b_pointnet2_cp310_b5ceb6d_v2_20261018/wheelhouse/pointnet2_ops-3.0.0-cp310-cp310-linux_x86_64.whl', 'bytes': 123291, 'sha256': '530496a0d1d5dea6151a466b7c0874632322223308a7016910fb1bfbaaaab1e5'}, {'path': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'bytes': 17331920, 'sha256': '01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/base_model.yaml', 'bytes': 2082, 'sha256': 'e18feb90d782506f864560ce5513b3077f840f9d6365308b03493f80f8c57dc4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'}]), hashed_bytes=total)))