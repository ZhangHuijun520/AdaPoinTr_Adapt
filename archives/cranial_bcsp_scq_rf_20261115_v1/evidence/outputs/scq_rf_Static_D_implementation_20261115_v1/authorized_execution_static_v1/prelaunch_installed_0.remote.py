from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/bcsp_scq_rf_Static_D_training_entry_v1.py', 'bytes': 30513, 'sha256': '20ad874ebb11c6b42f3d72399245a28c6936eef62e8d97491ad20d8bf1d733b6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_D_formal_freeze_v1.json', 'bytes': 11442, 'sha256': '51cfba6ead7ab7d15fe3b2fd2fd7463fa6105084fd9a76fb2071d115a6c66cb4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/SCQ_RF_Static_D_training_execution_request_v1.json', 'bytes': 48754, 'sha256': 'b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/bcsp_scq_rf_Static_D_training_entry_v1.py', 'bytes': 30513, 'sha256': '20ad874ebb11c6b42f3d72399245a28c6936eef62e8d97491ad20d8bf1d733b6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_C_formal_freeze_v1.json', 'bytes': 10285, 'sha256': '10fc886d1523b53c170120d59c645159a5c19d8da78f0f34856db680db6e6d56'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_D_formal_freeze_v1.json', 'bytes': 11442, 'sha256': '51cfba6ead7ab7d15fe3b2fd2fd7463fa6105084fd9a76fb2071d115a6c66cb4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/SCQ_RF_Static_D_training_execution_request_v1.json', 'bytes': 48754, 'sha256': 'b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'}]), hashed_bytes=total)))