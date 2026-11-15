from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/SCQ_RF_artificial_cuda_execution_request_v2.json', 'bytes': 31290, 'sha256': '09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/static_review_v2.json', 'bytes': 3031, 'sha256': '2f4a835a88f6c8c0118b4ecebedd1c19d965cc329b9f1e458d6ddaefc9d76f9c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/test_rf_cuda_entry_cpu_v2.py', 'bytes': 14344, 'sha256': '727346266d54723183012ae1aadf5d7a6e9796878e452df3f9098f4e13cb2169'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/SCQ_RF_artificial_cuda_execution_request_v2.json', 'bytes': 31290, 'sha256': '09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/static_review_v2.json', 'bytes': 3031, 'sha256': '2f4a835a88f6c8c0118b4ecebedd1c19d965cc329b9f1e458d6ddaefc9d76f9c'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/test_rf_cuda_entry_cpu_v2.py', 'bytes': 14344, 'sha256': '727346266d54723183012ae1aadf5d7a6e9796878e452df3f9098f4e13cb2169'}]), hashed_bytes=total)))