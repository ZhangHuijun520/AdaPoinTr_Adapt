from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/test_scq_rf_Sref_C_startup_chain_cpu_v4.py', 'bytes': 22796, 'sha256': 'fc76821b8145486c8edd2e26f43e9e17cfb5391004b5915603c6363d4a489543'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/training_CPU_result_v4.json', 'bytes': 3360, 'sha256': '656572126b48f52a380ca2d0f8bfe519958d61fcc1b609d77e07de9659ae493b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/training_entry_P3_v3.json', 'bytes': 3251, 'sha256': 'b8cc6a8e51d13f6ccef945a708877a40a2516b9e0717a3b1d01404052344d597'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/test_scq_rf_Sref_C_startup_chain_cpu_v4.py', 'bytes': 22796, 'sha256': 'fc76821b8145486c8edd2e26f43e9e17cfb5391004b5915603c6363d4a489543'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/training_CPU_result_v4.json', 'bytes': 3360, 'sha256': '656572126b48f52a380ca2d0f8bfe519958d61fcc1b609d77e07de9659ae493b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/training_entry_P3_v3.json', 'bytes': 3251, 'sha256': 'b8cc6a8e51d13f6ccef945a708877a40a2516b9e0717a3b1d01404052344d597'}]), hashed_bytes=total)))