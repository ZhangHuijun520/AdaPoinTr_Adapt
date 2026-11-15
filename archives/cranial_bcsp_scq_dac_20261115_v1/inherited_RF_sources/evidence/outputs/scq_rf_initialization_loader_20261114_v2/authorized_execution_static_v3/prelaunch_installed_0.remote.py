from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/bcsp_scq_rf_residual_v2.py', 'bytes': 4596, 'sha256': 'c50cbdb0986fafe3ff2309ef8c02d74fdc5e651218c71f4bb13a87bacefc726a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/entry_P3_v3.json', 'bytes': 5205, 'sha256': '2f6e7e5fc6ac5e2aa6eb1f53240d1cd585e99e5f8769c5e8da3a44ce6d749098'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/implementation_P3_v3.json', 'bytes': 3881, 'sha256': '3b9011abcbe8d39510338349488e2cebaf90bd13ca3fe7735bc44ec31401ad2f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/loader_CPU_result_v2.json', 'bytes': 3847, 'sha256': 'd0760d5c4504d589ea362a2f5a64d1296812ae9f046296188fdbb17ebbd82e2e'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/bcsp_scq_rf_residual_v2.py', 'bytes': 4596, 'sha256': 'c50cbdb0986fafe3ff2309ef8c02d74fdc5e651218c71f4bb13a87bacefc726a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/entry_P3_v3.json', 'bytes': 5205, 'sha256': '2f6e7e5fc6ac5e2aa6eb1f53240d1cd585e99e5f8769c5e8da3a44ce6d749098'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/implementation_P3_v3.json', 'bytes': 3881, 'sha256': '3b9011abcbe8d39510338349488e2cebaf90bd13ca3fe7735bc44ec31401ad2f'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3/loader_CPU_result_v2.json', 'bytes': 3847, 'sha256': 'd0760d5c4504d589ea362a2f5a64d1296812ae9f046296188fdbb17ebbd82e2e'}]), hashed_bytes=total)))