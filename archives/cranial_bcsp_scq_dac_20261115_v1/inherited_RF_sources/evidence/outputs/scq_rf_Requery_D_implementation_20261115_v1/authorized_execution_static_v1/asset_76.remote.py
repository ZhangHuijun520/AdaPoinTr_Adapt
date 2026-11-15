from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/exposure.json', 'bytes': 19465, 'sha256': '1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json', 'bytes': 39531, 'sha256': 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_bridge_v1.py', 'bytes': 848, 'sha256': '97b8b25b146f2db87794ca739e8b822d5a6ebf258bf2a424ede73ae37e6e46bf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_FoldD_metadata_readiness_v1.json', 'bytes': 1390, 'sha256': '0dbd94626c75c0d5a6afeba138026849777dc3804beaab63a705eae6bc6e0e61'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/exposure.json', 'bytes': 19465, 'sha256': '1203296e9aed5f177fe51b2278703828f3c14ed7d10a7f379ea39208e52dfb42'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json', 'bytes': 39531, 'sha256': 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_bridge_v1.py', 'bytes': 848, 'sha256': '97b8b25b146f2db87794ca739e8b822d5a6ebf258bf2a424ede73ae37e6e46bf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_FoldD_metadata_readiness_v1.json', 'bytes': 1390, 'sha256': '0dbd94626c75c0d5a6afeba138026849777dc3804beaab63a705eae6bc6e0e61'}]), hashed_bytes=total)))