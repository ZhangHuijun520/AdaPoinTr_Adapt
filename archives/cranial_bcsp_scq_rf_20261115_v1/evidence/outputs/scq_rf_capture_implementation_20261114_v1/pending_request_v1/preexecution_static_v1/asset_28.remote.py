from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_input_index_v2.json', 'bytes': 408919, 'sha256': 'ba3dae2ddb30db2cdbc1811f28d8d48949fd9ed1b34678288443a19c58216a6e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_scope_v1.json', 'bytes': 1009, 'sha256': '441c20f47c0231604e41b69e501d47f6fa82de0923aafef8e221c9e5234fa032'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/implementation_P3_v2.json', 'bytes': 4948, 'sha256': '5efa9f4a96ffa8a0f43a4a99edb352400dfc07042c319ebb6a8c93138684cedb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_B_C_training_audit_v1.json', 'bytes': 12245, 'sha256': '553cfaaecd437442692b35ec9d257c9e4defab7bd79432f4a7170e5696e98cf0'}]:
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
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_input_index_v2.json', 'bytes': 408919, 'sha256': 'ba3dae2ddb30db2cdbc1811f28d8d48949fd9ed1b34678288443a19c58216a6e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_scope_v1.json', 'bytes': 1009, 'sha256': '441c20f47c0231604e41b69e501d47f6fa82de0923aafef8e221c9e5234fa032'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/implementation_P3_v2.json', 'bytes': 4948, 'sha256': '5efa9f4a96ffa8a0f43a4a99edb352400dfc07042c319ebb6a8c93138684cedb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_B_C_training_audit_v1.json', 'bytes': 12245, 'sha256': '553cfaaecd437442692b35ec9d257c9e4defab7bd79432f4a7170e5696e98cf0'}]), hashed_bytes=total)))