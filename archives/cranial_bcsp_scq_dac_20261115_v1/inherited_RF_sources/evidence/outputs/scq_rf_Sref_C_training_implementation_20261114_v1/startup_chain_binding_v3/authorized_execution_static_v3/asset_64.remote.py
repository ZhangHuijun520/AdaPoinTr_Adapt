from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/FoldC_readiness_v1.json', 'bytes': 963, 'sha256': '281f2494f335fba0d4f6069b9f1b04d05325236f479dd2a64c3a6350f0da0dc6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_six_run_contract_v1.json', 'bytes': 4173, 'sha256': '52c1ae9eda38cf513a34af449b81da980e43ba1b9fe675f4bc9fda4ef1189735'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_training_bridge_v1.py', 'bytes': 703, 'sha256': '9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/FoldC_readiness_v1.json', 'bytes': 963, 'sha256': '281f2494f335fba0d4f6069b9f1b04d05325236f479dd2a64c3a6350f0da0dc6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_six_run_contract_v1.json', 'bytes': 4173, 'sha256': '52c1ae9eda38cf513a34af449b81da980e43ba1b9fe675f4bc9fda4ef1189735'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/bcsp_scq_rf_training_bridge_v1.py', 'bytes': 703, 'sha256': '9f282d1ce07e9c89ba7cac246d99c2c9f0ac2086f1f5de80151ae2a73723c6dd'}]), hashed_bytes=total)))