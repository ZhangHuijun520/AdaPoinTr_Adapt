from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/static_review_v1.json', 'bytes': 1373, 'sha256': 'f6ef7735dd3f2667d92a6323f4ff81826b8fd3d0b40f54742ac6d169871bb23c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/test_RF_Requery_D_entry_cpu_v1.py', 'bytes': 24532, 'sha256': '5c911732aa1be5bd90bf2d1f2e1f352b68fe09fd12222fd1041199b999cb4c00'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/static_review_v1.json', 'bytes': 1373, 'sha256': 'f6ef7735dd3f2667d92a6323f4ff81826b8fd3d0b40f54742ac6d169871bb23c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/test_RF_Requery_D_entry_cpu_v1.py', 'bytes': 24532, 'sha256': '5c911732aa1be5bd90bf2d1f2e1f352b68fe09fd12222fd1041199b999cb4c00'}]), hashed_bytes=total)))