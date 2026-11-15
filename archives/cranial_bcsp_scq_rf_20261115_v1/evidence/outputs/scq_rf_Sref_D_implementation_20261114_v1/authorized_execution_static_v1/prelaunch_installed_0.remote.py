from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/bcsp_scq_rf_Sref_D_training_entry_v1.py', 'bytes': 23501, 'sha256': 'c990e9446cc30ddda100dd60c5a991b3bad5263dcb0ae6baab97aefe8de11fbc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_FoldD_metadata_readiness_v1.json', 'bytes': 1390, 'sha256': '0dbd94626c75c0d5a6afeba138026849777dc3804beaab63a705eae6bc6e0e61'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_six_run_contract_v2.json', 'bytes': 6219, 'sha256': 'bc0d77d2865c59c0fcd95cc81b83d585fb93f052103675f9b532d62abf5acce8'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/bcsp_scq_rf_Sref_D_training_entry_v1.py', 'bytes': 23501, 'sha256': 'c990e9446cc30ddda100dd60c5a991b3bad5263dcb0ae6baab97aefe8de11fbc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_FoldD_metadata_readiness_v1.json', 'bytes': 1390, 'sha256': '0dbd94626c75c0d5a6afeba138026849777dc3804beaab63a705eae6bc6e0e61'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_six_run_contract_v2.json', 'bytes': 6219, 'sha256': 'bc0d77d2865c59c0fcd95cc81b83d585fb93f052103675f9b532d62abf5acce8'}]), hashed_bytes=total)))