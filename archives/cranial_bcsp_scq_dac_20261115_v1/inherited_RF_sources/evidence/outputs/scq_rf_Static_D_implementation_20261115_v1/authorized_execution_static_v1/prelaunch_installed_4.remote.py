from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_accepted_device_migration_v1.json', 'bytes': 3162, 'sha256': '1db4e71e5f3fe8f00379856cbb47a7b0307b394217685408577b38964d5a06b9'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_C_formal_freeze_v1.json', 'bytes': 8448, 'sha256': '1d5370c94ba1ad2435687e803a8823adce23c29ab09a27ba4b3fb377bf8d2149'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Sref_D_formal_freeze_v1.json', 'bytes': 9906, 'sha256': 'c48dbb53070b1c996d77c0272ce0aef03186eb93153855002cbd03a51a98f9dd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_C_formal_freeze_v1.json', 'bytes': 9221, 'sha256': 'fdc804bcde639e9dc6074584ddd93d70e8144d7ccecb2dedc2575aa7a91c1cab'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/Static_D_accepted_device_migration_v1.json', 'bytes': 3162, 'sha256': '1db4e71e5f3fe8f00379856cbb47a7b0307b394217685408577b38964d5a06b9'}]), hashed_bytes=total)))