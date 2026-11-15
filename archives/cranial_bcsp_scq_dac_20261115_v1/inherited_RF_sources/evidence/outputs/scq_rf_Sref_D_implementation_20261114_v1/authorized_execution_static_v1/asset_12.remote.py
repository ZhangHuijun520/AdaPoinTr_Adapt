from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/qualified_SCQ_C_8192_v1.json', 'bytes': 1641, 'sha256': 'b51fc4d88c63fb8a928868bf94d7c3eef3aba117a7de1138d2cdd2aa6c643cd4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/real_data_qc_verification_v1.json', 'bytes': 5769, 'sha256': '54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/qualified_SCQ_C_8192_v1.json', 'bytes': 1641, 'sha256': 'b51fc4d88c63fb8a928868bf94d7c3eef3aba117a7de1138d2cdd2aa6c643cd4'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/real_data_qc_verification_v1.json', 'bytes': 5769, 'sha256': '54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b'}]), hashed_bytes=total)))