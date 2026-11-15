from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/training_CPU_result_v1.json', 'bytes': 4044, 'sha256': 'a263f5050de39eaa18f8249baab0dacb9d42c59ccebc820920f5e475c943cbde'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/training_entry_P3_v1.json', 'bytes': 4811, 'sha256': 'd6d94a7d53f25016a82f04637d41399840af8cdbcf4e81a40f046ddde755a642'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/training_CPU_result_v1.json', 'bytes': 4044, 'sha256': 'a263f5050de39eaa18f8249baab0dacb9d42c59ccebc820920f5e475c943cbde'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1/training_entry_P3_v1.json', 'bytes': 4811, 'sha256': 'd6d94a7d53f25016a82f04637d41399840af8cdbcf4e81a40f046ddde755a642'}]), hashed_bytes=total)))