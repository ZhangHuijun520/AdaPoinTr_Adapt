from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/static_review_v1.json', 'bytes': 1371, 'sha256': '4a60ca2fe826007a38ce9951526ae788837053809b2a600e2d689b102eaeca36'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/test_RF_Requery_C_entry_cpu_v1.py', 'bytes': 23808, 'sha256': '7e770db4149b5454132ce390b9236da23f19df33a24736d2475130152d288e5f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3804, 'sha256': '1b1df4be7f68944f2df16115a15e7edf9092d93d67c421c31e982c40275893ee'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/static_review_v1.json', 'bytes': 1371, 'sha256': '4a60ca2fe826007a38ce9951526ae788837053809b2a600e2d689b102eaeca36'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/test_RF_Requery_C_entry_cpu_v1.py', 'bytes': 23808, 'sha256': '7e770db4149b5454132ce390b9236da23f19df33a24736d2475130152d288e5f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/training_CPU_result_v1.json', 'bytes': 3804, 'sha256': '1b1df4be7f68944f2df16115a15e7edf9092d93d67c421c31e982c40275893ee'}]), hashed_bytes=total)))