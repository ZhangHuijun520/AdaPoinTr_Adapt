from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/test_RF_Sref_D_entry_cpu_v1.py', 'bytes': 23336, 'sha256': '6595c2cfa45b99266cb31c66b9507f687d4a66b4aa1601ae964fc87ee49f13b0'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3498, 'sha256': '44eeb845ba8f7bd71c0f0bb60c703dbc3b12fdfe21e48b7215869384c9e92ca3'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3084, 'sha256': 'd8b05b78ca0e32d730dcc800ee8da52ce76d81d45d2633cf3f40e8f61226e1b8'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/test_RF_Sref_D_entry_cpu_v1.py', 'bytes': 23336, 'sha256': '6595c2cfa45b99266cb31c66b9507f687d4a66b4aa1601ae964fc87ee49f13b0'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3498, 'sha256': '44eeb845ba8f7bd71c0f0bb60c703dbc3b12fdfe21e48b7215869384c9e92ca3'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/training_entry_P3_v1.json', 'bytes': 3084, 'sha256': 'd8b05b78ca0e32d730dcc800ee8da52ce76d81d45d2633cf3f40e8f61226e1b8'}]), hashed_bytes=total)))