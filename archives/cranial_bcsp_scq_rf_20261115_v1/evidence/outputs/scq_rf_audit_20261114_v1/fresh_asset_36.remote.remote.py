from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_freeze_audit_v1.json', 'bytes': 5949, 'sha256': 'f7fad610b67d96da91c02c6ff879f861d4b101851db5548b05b3117345512895'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_inventory_v1.json', 'bytes': 3683, 'sha256': '816b5e93b814c0f8ef1b210a481f1a6d6deaec0cbefe32585724c042719dcba9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_construction_v1.json', 'bytes': 1850, 'sha256': '6f5ec778f4a4e6cca73b472f3e5d3f2a332075387f0760f53a68ef15a96bfb85'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_freeze_audit_v1.json', 'bytes': 5949, 'sha256': 'f7fad610b67d96da91c02c6ff879f861d4b101851db5548b05b3117345512895'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_inventory_v1.json', 'bytes': 3683, 'sha256': '816b5e93b814c0f8ef1b210a481f1a6d6deaec0cbefe32585724c042719dcba9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_construction_v1.json', 'bytes': 1850, 'sha256': '6f5ec778f4a4e6cca73b472f3e5d3f2a332075387f0760f53a68ef15a96bfb85'}]), hashed_bytes=total)))