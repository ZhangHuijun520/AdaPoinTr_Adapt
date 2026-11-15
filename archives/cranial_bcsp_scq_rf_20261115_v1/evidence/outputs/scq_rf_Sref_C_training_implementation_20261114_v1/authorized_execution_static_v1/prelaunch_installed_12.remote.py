from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/test_scq_rf_Sref_C_entry_cpu_v2.py', 'bytes': 18385, 'sha256': '884151daf52e7793a19c0c1f318a19360d2507e0f62f86bdbbfd7cc671058cdb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/training_CPU_result_v2.json', 'bytes': 3180, 'sha256': '8319e055ca06924020cf826a03141f25aa5adeff0a0db38a8717f5ba18ad9fe3'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3866, 'sha256': '5b4e1c8fdcef8b3be71b00cde3b3d708742699038d8cbad430d4546a08e90c65'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/test_scq_rf_Sref_C_entry_cpu_v2.py', 'bytes': 18385, 'sha256': '884151daf52e7793a19c0c1f318a19360d2507e0f62f86bdbbfd7cc671058cdb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/training_CPU_result_v2.json', 'bytes': 3180, 'sha256': '8319e055ca06924020cf826a03141f25aa5adeff0a0db38a8717f5ba18ad9fe3'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3866, 'sha256': '5b4e1c8fdcef8b3be71b00cde3b3d708742699038d8cbad430d4546a08e90c65'}]), hashed_bytes=total)))