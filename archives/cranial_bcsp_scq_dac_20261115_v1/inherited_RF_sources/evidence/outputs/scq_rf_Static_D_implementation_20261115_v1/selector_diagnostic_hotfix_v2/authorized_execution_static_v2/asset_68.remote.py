from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/model_construction.json', 'bytes': 91077, 'sha256': 'b234da9681cf01f86f7e94300581050cdd06f3b1600f4fdae1289a06349c5f9d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/initialization.json', 'bytes': 289, 'sha256': '504fe1bcbb96978ad1f5e61d505faefd984bb1de42bb24862d1e1bade2a9aeaa'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/model_construction.json', 'bytes': 91077, 'sha256': 'b234da9681cf01f86f7e94300581050cdd06f3b1600f4fdae1289a06349c5f9d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/initialization.json', 'bytes': 289, 'sha256': '504fe1bcbb96978ad1f5e61d505faefd984bb1de42bb24862d1e1bade2a9aeaa'}]), hashed_bytes=total)))