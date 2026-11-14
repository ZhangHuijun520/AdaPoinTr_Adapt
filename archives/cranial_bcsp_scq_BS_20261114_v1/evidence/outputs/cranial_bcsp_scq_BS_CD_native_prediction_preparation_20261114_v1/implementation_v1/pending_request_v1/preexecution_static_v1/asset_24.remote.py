from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_freeze_audit_v1.json', 'bytes': 5949, 'sha256': 'f7fad610b67d96da91c02c6ff879f861d4b101851db5548b05b3117345512895'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_freeze_audit_v1.json', 'bytes': 5949, 'sha256': 'f7fad610b67d96da91c02c6ff879f861d4b101851db5548b05b3117345512895'}]), hashed_bytes=total)))