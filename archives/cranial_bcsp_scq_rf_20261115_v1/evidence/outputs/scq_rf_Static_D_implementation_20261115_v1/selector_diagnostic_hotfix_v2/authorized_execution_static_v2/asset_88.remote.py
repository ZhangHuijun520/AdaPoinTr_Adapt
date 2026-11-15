from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/model_construction.json', 'bytes': 96513, 'sha256': '9d7a9731463831e9f8b75c6e0f1a3ac6f337db674f83e14c1246a7da2ea06eb2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/initialization.json', 'bytes': 289, 'sha256': '8bbe1bcce803197b868ec3339fc9fe2bfb70c4f7c8e1d37751767f0033a4b31a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/exposure.json', 'bytes': 19465, 'sha256': '65907c12b1eeec2886b7581bd0c9515c831eff9d45e0ecd46ca384a34d6dc902'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json', 'bytes': 45310, 'sha256': '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/model_construction.json', 'bytes': 96513, 'sha256': '9d7a9731463831e9f8b75c6e0f1a3ac6f337db674f83e14c1246a7da2ea06eb2'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/initialization.json', 'bytes': 289, 'sha256': '8bbe1bcce803197b868ec3339fc9fe2bfb70c4f7c8e1d37751767f0033a4b31a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1/exposure.json', 'bytes': 19465, 'sha256': '65907c12b1eeec2886b7581bd0c9515c831eff9d45e0ecd46ca384a34d6dc902'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json', 'bytes': 45310, 'sha256': '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'}]), hashed_bytes=total)))