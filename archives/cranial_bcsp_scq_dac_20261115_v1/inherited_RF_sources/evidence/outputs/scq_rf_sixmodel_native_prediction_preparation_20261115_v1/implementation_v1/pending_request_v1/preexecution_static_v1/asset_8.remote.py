from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py', 'bytes': 29284, 'sha256': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}]), hashed_bytes=total)))