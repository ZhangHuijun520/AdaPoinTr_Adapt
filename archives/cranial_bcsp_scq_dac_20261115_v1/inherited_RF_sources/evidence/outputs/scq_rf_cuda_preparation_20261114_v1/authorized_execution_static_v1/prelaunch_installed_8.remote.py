from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/SCQ_RF_artificial_cuda_execution_request_v1.json', 'bytes': 29211, 'sha256': '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/test_rf_cuda_entry_cpu_v1.py', 'bytes': 11969, 'sha256': 'd250d53af69dc09660e734ca285afd43dc98f1f0fc792de095acccbbd1bbf1af'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/test_scq_rf_cpu_v2.py', 'bytes': 22432, 'sha256': '7e5f4e8573d9a2a4d1046dada1e0e5260004ca51980d4342b3c0d24f23061924'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/rf_initialization_v1.bin', 'bytes': 924684, 'sha256': 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/SCQ_RF_artificial_cuda_execution_request_v1.json', 'bytes': 29211, 'sha256': '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/test_rf_cuda_entry_cpu_v1.py', 'bytes': 11969, 'sha256': 'd250d53af69dc09660e734ca285afd43dc98f1f0fc792de095acccbbd1bbf1af'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/test_scq_rf_cpu_v2.py', 'bytes': 22432, 'sha256': '7e5f4e8573d9a2a4d1046dada1e0e5260004ca51980d4342b3c0d24f23061924'}]), hashed_bytes=total)))