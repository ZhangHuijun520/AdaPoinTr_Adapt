from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_cuda_admission_v1.py', 'bytes': 27074, 'sha256': 'a46c10023766933581f7113141db4e31a5c8fb47c107ece82901cdc58cc8dc47'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_residual_v1.py', 'bytes': 4155, 'sha256': 'e8d00efd6b7b40edf599972d75cf98f5e9f0fa725fd969256d2f3b2329f925ef'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/entry_CPU_result_v1.json', 'bytes': 174789, 'sha256': 'd04903d2f5f560fd831de7042297b8cc0ada8319df8cf689ba53fa7d9b28fe48'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_cuda_admission_v1.py', 'bytes': 27074, 'sha256': 'a46c10023766933581f7113141db4e31a5c8fb47c107ece82901cdc58cc8dc47'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_residual_v1.py', 'bytes': 4155, 'sha256': 'e8d00efd6b7b40edf599972d75cf98f5e9f0fa725fd969256d2f3b2329f925ef'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/entry_CPU_result_v1.json', 'bytes': 174789, 'sha256': 'd04903d2f5f560fd831de7042297b8cc0ada8319df8cf689ba53fa7d9b28fe48'}]), hashed_bytes=total)))