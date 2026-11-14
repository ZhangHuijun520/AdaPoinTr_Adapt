from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_residual_v1.py', 'bytes': 3552, 'sha256': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_factory_v1.py', 'bytes': 14176, 'sha256': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_cuda_admission_v3.py', 'bytes': 23393, 'sha256': 'fe7fc491cdeed22ba939b1a0c45b08905f8ebdb67d5f09b41b6f1975d2630ad6'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_residual_v1.py', 'bytes': 3552, 'sha256': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_factory_v1.py', 'bytes': 14176, 'sha256': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_gradient_quantification_20261105_v1/exact_utc_resource_v1.py', 'bytes': 3563, 'sha256': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_cuda_admission_v3.py', 'bytes': 23393, 'sha256': 'fe7fc491cdeed22ba939b1a0c45b08905f8ebdb67d5f09b41b6f1975d2630ad6'}]), hashed_bytes=total)))