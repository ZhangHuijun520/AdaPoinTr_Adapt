from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/initialization.json', 'bytes': 289, 'sha256': '424cd95d574c724d8996b285e31787d5c4a4c3ab84e6b6db74a0aafab9c53728'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/exposure.json', 'bytes': 19465, 'sha256': '65907c12b1eeec2886b7581bd0c9515c831eff9d45e0ecd46ca384a34d6dc902'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/SCQ_RF_Sref_D_training_execution_request_v1.json', 'bytes': 36546, 'sha256': '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/initialization.json', 'bytes': 289, 'sha256': '424cd95d574c724d8996b285e31787d5c4a4c3ab84e6b6db74a0aafab9c53728'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/exposure.json', 'bytes': 19465, 'sha256': '65907c12b1eeec2886b7581bd0c9515c831eff9d45e0ecd46ca384a34d6dc902'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/SCQ_RF_Sref_D_training_execution_request_v1.json', 'bytes': 36546, 'sha256': '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'}]), hashed_bytes=total)))