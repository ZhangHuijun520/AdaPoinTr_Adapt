from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/entry_CPU_result_v2.json', 'bytes': 192624, 'sha256': '568eb992df25912cd95647bee2fff8421e69215091fcea7144c8975fcd504321'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/entry_P3_v2.json', 'bytes': 4612, 'sha256': '7a87cfaa160ab0fee3fabbc2535e49fd7b905d0bd6731dfabf2f6e63da12e225'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/prior_failed_freeze_audit_v1.json', 'bytes': 16350, 'sha256': '1d8f2dce8fe3dbf233315e471c7308e5d38b7484836c5cbf4326c1ec14e04412'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/entry_CPU_result_v2.json', 'bytes': 192624, 'sha256': '568eb992df25912cd95647bee2fff8421e69215091fcea7144c8975fcd504321'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/entry_P3_v2.json', 'bytes': 4612, 'sha256': '7a87cfaa160ab0fee3fabbc2535e49fd7b905d0bd6731dfabf2f6e63da12e225'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/prior_failed_freeze_audit_v1.json', 'bytes': 16350, 'sha256': '1d8f2dce8fe3dbf233315e471c7308e5d38b7484836c5cbf4326c1ec14e04412'}]), hashed_bytes=total)))