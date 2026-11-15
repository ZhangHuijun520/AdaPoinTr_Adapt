from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/static_review_v1.json', 'bytes': 1438, 'sha256': 'e997f79ff2d25e3d257ca421e91e3d06ffc75d4faa45b3d97be9c3ad96b2c0b5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/test_RF_Static_C_entry_cpu_v1.py', 'bytes': 21895, 'sha256': 'a64d22b6dda5b4a1e61b52c9350076d137280e72a7a6026eed552f5d9ddfe8ee'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3428, 'sha256': '61be60d146b61bee073bb6a23265338ae7de236d7e54a328e0e6998fe61e16fa'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3361, 'sha256': 'e5bc6bb863567a5dfa2c8bed880e5108e19e22796f0f9ed7923097e337093b78'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/static_review_v1.json', 'bytes': 1438, 'sha256': 'e997f79ff2d25e3d257ca421e91e3d06ffc75d4faa45b3d97be9c3ad96b2c0b5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/test_RF_Static_C_entry_cpu_v1.py', 'bytes': 21895, 'sha256': 'a64d22b6dda5b4a1e61b52c9350076d137280e72a7a6026eed552f5d9ddfe8ee'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3428, 'sha256': '61be60d146b61bee073bb6a23265338ae7de236d7e54a328e0e6998fe61e16fa'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3361, 'sha256': 'e5bc6bb863567a5dfa2c8bed880e5108e19e22796f0f9ed7923097e337093b78'}]), hashed_bytes=total)))