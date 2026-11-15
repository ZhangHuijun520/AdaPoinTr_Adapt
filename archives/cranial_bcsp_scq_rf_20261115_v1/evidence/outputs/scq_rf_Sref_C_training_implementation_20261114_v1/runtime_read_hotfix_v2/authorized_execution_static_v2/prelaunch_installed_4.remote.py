from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/test_scq_rf_Sref_C_runtime_read_cpu_v3.py', 'bytes': 20070, 'sha256': '049cfb457847fd1ef168ca2a1cad4f6337ea81e4124f88114d834abb8442ac0d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/training_CPU_result_v3.json', 'bytes': 3211, 'sha256': 'e738ed4730b222b3a4eb875e99cf3c8f0c2f58fb3e788403a2687cf969b1394f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/training_entry_P3_v2.json', 'bytes': 3035, 'sha256': '5ea17e7344a3bf52a65cc70f3869845a5dba16a28d4b45301728d411dd79196b'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/test_scq_rf_Sref_C_runtime_read_cpu_v3.py', 'bytes': 20070, 'sha256': '049cfb457847fd1ef168ca2a1cad4f6337ea81e4124f88114d834abb8442ac0d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/training_CPU_result_v3.json', 'bytes': 3211, 'sha256': 'e738ed4730b222b3a4eb875e99cf3c8f0c2f58fb3e788403a2687cf969b1394f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v2/training_entry_P3_v2.json', 'bytes': 3035, 'sha256': '5ea17e7344a3bf52a65cc70f3869845a5dba16a28d4b45301728d411dd79196b'}]), hashed_bytes=total)))