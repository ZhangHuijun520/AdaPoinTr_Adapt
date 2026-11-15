from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/SCQ_RF_Sref_D_training_execution_request_v1.json', 'bytes': 36546, 'sha256': '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/static_review_v1.json', 'bytes': 1880, 'sha256': '8e009ac54c9ad81c2b1a4e0e43b4c93269d37cbb623f8b610482595bebb331fd'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/SCQ_RF_Sref_D_training_execution_request_v1.json', 'bytes': 36546, 'sha256': '888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/static_review_v1.json', 'bytes': 1880, 'sha256': '8e009ac54c9ad81c2b1a4e0e43b4c93269d37cbb623f8b610482595bebb331fd'}]), hashed_bytes=total)))