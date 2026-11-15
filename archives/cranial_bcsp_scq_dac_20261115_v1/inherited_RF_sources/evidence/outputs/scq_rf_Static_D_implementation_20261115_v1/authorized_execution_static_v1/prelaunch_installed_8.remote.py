from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_current_identity_readiness_v1.json', 'bytes': 1387, 'sha256': '9d81e2ae2e4dc36eeb975d5e484912ee0993580031bd7533d030906466db9665'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/static_review_v1.json', 'bytes': 1403, 'sha256': '2dc29b0e2c68aeebf0289f2527b60efc57105fa525fa0937f19ebbc0bfc0c691'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/test_RF_Static_D_entry_cpu_v1.py', 'bytes': 25428, 'sha256': 'db846f5b14284ebf806ac1c6a17f6d5c38a96f75d63a9244dbba5d122cc5909d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/training_CPU_result_v1.json', 'bytes': 4421, 'sha256': 'e592fc0e43499e43463975a4a74ee986a135e659cd98659a6679baf376c07dd1'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_current_identity_readiness_v1.json', 'bytes': 1387, 'sha256': '9d81e2ae2e4dc36eeb975d5e484912ee0993580031bd7533d030906466db9665'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/static_review_v1.json', 'bytes': 1403, 'sha256': '2dc29b0e2c68aeebf0289f2527b60efc57105fa525fa0937f19ebbc0bfc0c691'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/test_RF_Static_D_entry_cpu_v1.py', 'bytes': 25428, 'sha256': 'db846f5b14284ebf806ac1c6a17f6d5c38a96f75d63a9244dbba5d122cc5909d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/training_CPU_result_v1.json', 'bytes': 4421, 'sha256': 'e592fc0e43499e43463975a4a74ee986a135e659cd98659a6679baf376c07dd1'}]), hashed_bytes=total)))