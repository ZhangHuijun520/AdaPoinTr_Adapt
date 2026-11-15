from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_inventory_v3.json', 'bytes': 14618, 'sha256': '1d2477ba21c88db3defa67165a9842faf71dfe6ff5c76ec7d775d5d1f6e5d921'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_inventory_v3.json', 'bytes': 14618, 'sha256': '1d2477ba21c88db3defa67165a9842faf71dfe6ff5c76ec7d775d5d1f6e5d921'}]), hashed_bytes=total)))