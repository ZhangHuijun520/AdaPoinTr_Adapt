from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_accepted_device_migration_v1.json', 'bytes': 3162, 'sha256': '1db4e71e5f3fe8f00379856cbb47a7b0307b394217685408577b38964d5a06b9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_current_identity_readiness_v1.json', 'bytes': 1387, 'sha256': '9d81e2ae2e4dc36eeb975d5e484912ee0993580031bd7533d030906466db9665'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_D_formal_freeze_v1.json', 'bytes': 11442, 'sha256': '51cfba6ead7ab7d15fe3b2fd2fd7463fa6105084fd9a76fb2071d115a6c66cb4'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_accepted_device_migration_v1.json', 'bytes': 3162, 'sha256': '1db4e71e5f3fe8f00379856cbb47a7b0307b394217685408577b38964d5a06b9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_current_identity_readiness_v1.json', 'bytes': 1387, 'sha256': '9d81e2ae2e4dc36eeb975d5e484912ee0993580031bd7533d030906466db9665'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Requery_D_formal_freeze_v1.json', 'bytes': 11442, 'sha256': '51cfba6ead7ab7d15fe3b2fd2fd7463fa6105084fd9a76fb2071d115a6c66cb4'}]), hashed_bytes=total)))