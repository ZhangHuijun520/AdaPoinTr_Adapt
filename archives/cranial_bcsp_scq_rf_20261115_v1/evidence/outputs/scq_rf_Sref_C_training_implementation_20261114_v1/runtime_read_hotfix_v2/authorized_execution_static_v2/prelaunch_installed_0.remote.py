from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/bcsp_scq_rf_Sref_C_training_entry_v2.py', 'bytes': 22097, 'sha256': '5a88b3ada34fe3f919166d73069d2831db2ccc365669444714a70757d7d39866'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/prior_failed_startup_freeze_v1.json', 'bytes': 17921, 'sha256': '0e5ce412a57d56d78e1beb12dd96647e5ef0cff1cc68298848e89de2c43a551a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/SCQ_RF_Sref_C_training_execution_request_v2.json', 'bytes': 35608, 'sha256': 'b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/static_review_v2.json', 'bytes': 1179, 'sha256': '5eceac6b1217e66e648b4612fee6f291f0366410f82373cec66519addbb44a2b'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/bcsp_scq_rf_Sref_C_training_entry_v2.py', 'bytes': 22097, 'sha256': '5a88b3ada34fe3f919166d73069d2831db2ccc365669444714a70757d7d39866'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/prior_failed_startup_freeze_v1.json', 'bytes': 17921, 'sha256': '0e5ce412a57d56d78e1beb12dd96647e5ef0cff1cc68298848e89de2c43a551a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/SCQ_RF_Sref_C_training_execution_request_v2.json', 'bytes': 35608, 'sha256': 'b387a08bd2de575723d8f89a6f0c7fb1665590108eed0ef62c00d28b8394d4f1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/static_review_v2.json', 'bytes': 1179, 'sha256': '5eceac6b1217e66e648b4612fee6f291f0366410f82373cec66519addbb44a2b'}]), hashed_bytes=total)))