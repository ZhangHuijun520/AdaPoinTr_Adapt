from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_runtime.py', 'bytes': 7320, 'sha256': '8cbb5389e074347f6bf6e776755d22bbdaedaf5dba5102d51866d1b1e49b3615'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_adapter.py', 'bytes': 7297, 'sha256': '2f7d3050cfb6ac2602cc17a95b860da2204daef2dfa63dab63d233e899b7dd55'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_runtime.py', 'bytes': 7320, 'sha256': '8cbb5389e074347f6bf6e776755d22bbdaedaf5dba5102d51866d1b1e49b3615'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/tools/bcsp_adapter.py', 'bytes': 7297, 'sha256': '2f7d3050cfb6ac2602cc17a95b860da2204daef2dfa63dab63d233e899b7dd55'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/bcsp_scq_rf_factory_v1.py', 'bytes': 3517, 'sha256': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}]), hashed_bytes=total)))