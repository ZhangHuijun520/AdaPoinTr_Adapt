from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/bcsp_scq_rf_Requery_D_training_entry_v1.py', 'bytes': 28479, 'sha256': '0a99d7ca7542b5ab5d4db4787d6ae2ad30e38b5f2d8f764292102b0c984e0c44'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json', 'bytes': 45310, 'sha256': '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/bcsp_scq_rf_Requery_D_training_entry_v1.py', 'bytes': 28479, 'sha256': '0a99d7ca7542b5ab5d4db4787d6ae2ad30e38b5f2d8f764292102b0c984e0c44'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/SCQ_RF_Requery_D_training_execution_request_v1.json', 'bytes': 45310, 'sha256': '4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]), hashed_bytes=total)))