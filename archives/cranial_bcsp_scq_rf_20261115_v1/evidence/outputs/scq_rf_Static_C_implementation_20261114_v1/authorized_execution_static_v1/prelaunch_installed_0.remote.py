from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_bridge_v1.py', 'bytes': 845, 'sha256': '67644f28ab5cd86dd587bf6cc4391b8a393e8af0fddee857398bc528e545b9a1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py', 'bytes': 25257, 'sha256': 'c457800917fbecd3fd3e7c38f73cc1971806a905dd874ecad3d3f96da3f9755f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json', 'bytes': 39531, 'sha256': 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_bridge_v1.py', 'bytes': 845, 'sha256': '67644f28ab5cd86dd587bf6cc4391b8a393e8af0fddee857398bc528e545b9a1'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py', 'bytes': 25257, 'sha256': 'c457800917fbecd3fd3e7c38f73cc1971806a905dd874ecad3d3f96da3f9755f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json', 'bytes': 39531, 'sha256': 'a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}]), hashed_bytes=total)))