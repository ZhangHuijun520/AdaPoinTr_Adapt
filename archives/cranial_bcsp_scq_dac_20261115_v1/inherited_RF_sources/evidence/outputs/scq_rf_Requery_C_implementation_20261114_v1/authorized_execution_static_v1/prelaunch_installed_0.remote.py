from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_bridge_v1.py', 'bytes': 848, 'sha256': '97b8b25b146f2db87794ca739e8b822d5a6ebf258bf2a424ede73ae37e6e46bf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_entry_v1.py', 'bytes': 27773, 'sha256': '26be687df4a74a71d45237402e91523750d8d089409d2e372c70ebef1d3c38f1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/SCQ_RF_Requery_C_training_execution_request_v1.json', 'bytes': 42742, 'sha256': '27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_bridge_v1.py', 'bytes': 848, 'sha256': '97b8b25b146f2db87794ca739e8b822d5a6ebf258bf2a424ede73ae37e6e46bf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/bcsp_scq_rf_Requery_C_training_entry_v1.py', 'bytes': 27773, 'sha256': '26be687df4a74a71d45237402e91523750d8d089409d2e372c70ebef1d3c38f1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/SCQ_RF_Requery_C_training_execution_request_v1.json', 'bytes': 42742, 'sha256': '27ef5aaa1c5aa1cc246e8c45597981d0233651dfbacf7621637a8a7b367a9497'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]), hashed_bytes=total)))