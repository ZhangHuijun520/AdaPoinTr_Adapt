from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/entry_P3_v1.json', 'bytes': 2645, 'sha256': '63ccd70d4d225076ff846f42e4e4de2c5b3f1c523dc0270c3e39115d4acb7b0d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/implementation_CPU_result_v2.json', 'bytes': 4640, 'sha256': '96fb1d0370b6ba3276b4275906e34fdc985487df9c9489db4d4bf22ef8397e2b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/implementation_P3_v2.json', 'bytes': 9059, 'sha256': '37b842a88a0a72a8b0d8b13f87603d0349384851b7d4b28ddaff36697b2f032a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_manifest_v1.json', 'bytes': 1185, 'sha256': 'b8bbbacde16fb3f1765f1cb56c1b2b17a8b8e09b0f80ca7a90c7df06530be957'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/entry_P3_v1.json', 'bytes': 2645, 'sha256': '63ccd70d4d225076ff846f42e4e4de2c5b3f1c523dc0270c3e39115d4acb7b0d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/implementation_CPU_result_v2.json', 'bytes': 4640, 'sha256': '96fb1d0370b6ba3276b4275906e34fdc985487df9c9489db4d4bf22ef8397e2b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/implementation_P3_v2.json', 'bytes': 9059, 'sha256': '37b842a88a0a72a8b0d8b13f87603d0349384851b7d4b28ddaff36697b2f032a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_manifest_v1.json', 'bytes': 1185, 'sha256': 'b8bbbacde16fb3f1765f1cb56c1b2b17a8b8e09b0f80ca7a90c7df06530be957'}]), hashed_bytes=total)))