from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/loader_static_review_v2.json', 'bytes': 2098, 'sha256': '0b26c5a5c78970b6314489a63d8ff1791093d72f53a9a9d095e4ed952f35a9e5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/prior_v2_failed_freeze_audit_v1.json', 'bytes': 14751, 'sha256': '71c4efa4c50fba1db2b9f6aac14763570620fa4c76bb5f05df09280e42365cb4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/SCQ_RF_artificial_cuda_execution_request_v3.json', 'bytes': 31882, 'sha256': '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/test_rf_byte_loader_cpu_v2.py', 'bytes': 10745, 'sha256': '5d58293183f540b6f7a808ae062bc7ce9a7f1f1a77fd6e24c68a9d57215816f6'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/loader_static_review_v2.json', 'bytes': 2098, 'sha256': '0b26c5a5c78970b6314489a63d8ff1791093d72f53a9a9d095e4ed952f35a9e5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/prior_v2_failed_freeze_audit_v1.json', 'bytes': 14751, 'sha256': '71c4efa4c50fba1db2b9f6aac14763570620fa4c76bb5f05df09280e42365cb4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/SCQ_RF_artificial_cuda_execution_request_v3.json', 'bytes': 31882, 'sha256': '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/test_rf_byte_loader_cpu_v2.py', 'bytes': 10745, 'sha256': '5d58293183f540b6f7a808ae062bc7ce9a7f1f1a77fd6e24c68a9d57215816f6'}]), hashed_bytes=total)))