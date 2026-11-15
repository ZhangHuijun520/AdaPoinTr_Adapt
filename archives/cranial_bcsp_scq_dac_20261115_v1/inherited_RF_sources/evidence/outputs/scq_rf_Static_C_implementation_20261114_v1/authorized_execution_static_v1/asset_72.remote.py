from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/exposure.json', 'bytes': 19465, 'sha256': '1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json', 'bytes': 35707, 'sha256': '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/exposure.json', 'bytes': 19465, 'sha256': '1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json', 'bytes': 35707, 'sha256': '6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88'}]), hashed_bytes=total)))