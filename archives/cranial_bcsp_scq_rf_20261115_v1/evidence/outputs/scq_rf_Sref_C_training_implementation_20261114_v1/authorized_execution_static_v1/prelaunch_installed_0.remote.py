from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_Sref_C_training_entry_v1.py', 'bytes': 22066, 'sha256': 'c6e29be6ac73cd0bb191c35115a00874635d0122d22aee334bd7b083324d11a7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_training_bridge_v1.py', 'bytes': 703, 'sha256': '9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/fixture_v2_static_review.json', 'bytes': 4907, 'sha256': 'cd99492f8fa9a18d4775c479ba13d982ff6e44d59b6369dd7846c9fb30c5ea20'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/FoldC_readiness_v1.json', 'bytes': 963, 'sha256': '281f2494f335fba0d4f6069b9f1b04d05325236f479dd2a64c3a6350f0da0dc6'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_Sref_C_training_entry_v1.py', 'bytes': 22066, 'sha256': 'c6e29be6ac73cd0bb191c35115a00874635d0122d22aee334bd7b083324d11a7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_training_bridge_v1.py', 'bytes': 703, 'sha256': '9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/fixture_v2_static_review.json', 'bytes': 4907, 'sha256': 'cd99492f8fa9a18d4775c479ba13d982ff6e44d59b6369dd7846c9fb30c5ea20'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/FoldC_readiness_v1.json', 'bytes': 963, 'sha256': '281f2494f335fba0d4f6069b9f1b04d05325236f479dd2a64c3a6350f0da0dc6'}]), hashed_bytes=total)))