from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/bcsp_lqi_decoder_v1.py', 'bytes': 6053, 'sha256': '92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/bcsp_lqi_factory_v1.py', 'bytes': 3864, 'sha256': '56d4cbe89660106f255a0d58e28c7cbaf38374c7788219d5a21779bd97aaf106'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_residual_v1.py', 'bytes': 3552, 'sha256': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_factory_v1.py', 'bytes': 14176, 'sha256': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/bcsp_lqi_decoder_v1.py', 'bytes': 6053, 'sha256': '92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/bcsp_lqi_factory_v1.py', 'bytes': 3864, 'sha256': '56d4cbe89660106f255a0d58e28c7cbaf38374c7788219d5a21779bd97aaf106'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_residual_v1.py', 'bytes': 3552, 'sha256': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_factory_v1.py', 'bytes': 14176, 'sha256': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5'}]), hashed_bytes=total)))