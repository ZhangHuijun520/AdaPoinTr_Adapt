from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/bcsp_scq_rf_Static_D_training_entry_v2.py', 'bytes': 31969, 'sha256': 'ef1e432b31d1db10a7cf03d9c962cfb9b259704e63a1e2b2d2b7404adac3c3aa'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/fixture_correction_review_v3.json', 'bytes': 1515, 'sha256': 'a232b0ba0eb13d16d8bd7b6ca5dcd1df000d7182b22b49fe0e62bb2a70018502'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/SCQ_RF_Static_D_training_execution_request_v2.json', 'bytes': 51247, 'sha256': '9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/Static_D_v1_failed_freeze_v1.json', 'bytes': 10853, 'sha256': 'a63f7037da4b9e2d74d8bd4a31944e9b3cf44823b7ade4430c484dc9547a703b'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/bcsp_scq_rf_Static_D_training_entry_v2.py', 'bytes': 31969, 'sha256': 'ef1e432b31d1db10a7cf03d9c962cfb9b259704e63a1e2b2d2b7404adac3c3aa'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/fixture_correction_review_v3.json', 'bytes': 1515, 'sha256': 'a232b0ba0eb13d16d8bd7b6ca5dcd1df000d7182b22b49fe0e62bb2a70018502'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/SCQ_RF_Static_D_training_execution_request_v2.json', 'bytes': 51247, 'sha256': '9d7ac459e9a969c36df67ddaee4c5c0aaac2c68b322dcf58097c54f59caa402b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/Static_D_v1_failed_freeze_v1.json', 'bytes': 10853, 'sha256': 'a63f7037da4b9e2d74d8bd4a31944e9b3cf44823b7ade4430c484dc9547a703b'}]), hashed_bytes=total)))