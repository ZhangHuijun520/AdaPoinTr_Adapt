from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/static_review_v2.json', 'bytes': 965, 'sha256': 'dc5edc1bc47f50e785274ae54c26268b035a027d7559ebbbe9c950cbf0947e08'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/test_Static_D_selector_diagnostic_cpu_v3.py', 'bytes': 29499, 'sha256': '60c352ae921d3a88c2e253f58a21e813a8d423ed3567e733bc615d59f3570fcd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/training_CPU_result_v3.json', 'bytes': 5035, 'sha256': '301b071e36f15f4f278e061d521b6dbda2696206f72d19c0e02ef70a538aafcc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/training_entry_P3_v2.json', 'bytes': 3637, 'sha256': '3f45cff66affdaae896f4626da37782c24952f15cc17be7096478ad0dedd1c23'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/static_review_v2.json', 'bytes': 965, 'sha256': 'dc5edc1bc47f50e785274ae54c26268b035a027d7559ebbbe9c950cbf0947e08'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/test_Static_D_selector_diagnostic_cpu_v3.py', 'bytes': 29499, 'sha256': '60c352ae921d3a88c2e253f58a21e813a8d423ed3567e733bc615d59f3570fcd'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/training_CPU_result_v3.json', 'bytes': 5035, 'sha256': '301b071e36f15f4f278e061d521b6dbda2696206f72d19c0e02ef70a538aafcc'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2/training_entry_P3_v2.json', 'bytes': 3637, 'sha256': '3f45cff66affdaae896f4626da37782c24952f15cc17be7096478ad0dedd1c23'}]), hashed_bytes=total)))