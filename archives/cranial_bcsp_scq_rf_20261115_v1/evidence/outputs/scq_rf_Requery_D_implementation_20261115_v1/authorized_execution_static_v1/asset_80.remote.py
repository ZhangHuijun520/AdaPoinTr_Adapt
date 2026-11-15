from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_six_run_contract_v2.json', 'bytes': 6219, 'sha256': 'bc0d77d2865c59c0fcd95cc81b83d585fb93f052103675f9b532d62abf5acce8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/shared_order_foldD_seed0_v1.json', 'bytes': 1248506, 'sha256': '4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/qualified_SCQ_D_8192_v1.json', 'bytes': 1641, 'sha256': '2aa5848b261e046b758a832485a60b80a2d85d152b573b99fafb07fe6d3d5be7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/model_construction.json', 'bytes': 91077, 'sha256': 'b234da9681cf01f86f7e94300581050cdd06f3b1600f4fdae1289a06349c5f9d'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/RF_six_run_contract_v2.json', 'bytes': 6219, 'sha256': 'bc0d77d2865c59c0fcd95cc81b83d585fb93f052103675f9b532d62abf5acce8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/shared_order_foldD_seed0_v1.json', 'bytes': 1248506, 'sha256': '4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/qualified_SCQ_D_8192_v1.json', 'bytes': 1641, 'sha256': '2aa5848b261e046b758a832485a60b80a2d85d152b573b99fafb07fe6d3d5be7'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1/model_construction.json', 'bytes': 91077, 'sha256': 'b234da9681cf01f86f7e94300581050cdd06f3b1600f4fdae1289a06349c5f9d'}]), hashed_bytes=total)))