from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py', 'bytes': 22450, 'sha256': 'bc01d750489002949bd442bcd806e8340d272ce7dfe16727ede8ee54f15d4adf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/prior_failed_startup_freeze_v2.json', 'bytes': 18098, 'sha256': 'b5c6519257767c25cd5dffee06f7dc15fc34402f93bd27522040f4147757dec4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json', 'bytes': 35707, 'sha256': '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/static_review_v3.json', 'bytes': 1229, 'sha256': '477ae4797fed73f97c0b011affc393f1b1a563585edf7157cdd9f9d8186b2fa1'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py', 'bytes': 22450, 'sha256': 'bc01d750489002949bd442bcd806e8340d272ce7dfe16727ede8ee54f15d4adf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/prior_failed_startup_freeze_v2.json', 'bytes': 18098, 'sha256': 'b5c6519257767c25cd5dffee06f7dc15fc34402f93bd27522040f4147757dec4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json', 'bytes': 35707, 'sha256': '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/static_review_v3.json', 'bytes': 1229, 'sha256': '477ae4797fed73f97c0b011affc393f1b1a563585edf7157cdd9f9d8186b2fa1'}]), hashed_bytes=total)))