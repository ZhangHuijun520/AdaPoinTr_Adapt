from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_inventory_v1.json', 'bytes': 3683, 'sha256': '816b5e93b814c0f8ef1b210a481f1a6d6deaec0cbefe32585724c042719dcba9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_construction_v1.json', 'bytes': 1850, 'sha256': '6f5ec778f4a4e6cca73b472f3e5d3f2a332075387f0760f53a68ef15a96bfb85'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_completion_v1.json', 'bytes': 246287, 'sha256': '935f92eebd048e7519a9f227bf6bd0434f21b7053a11b229464adac878fcc2eb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_request_v1.json', 'bytes': 29059, 'sha256': '0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_inventory_v1.json', 'bytes': 3683, 'sha256': '816b5e93b814c0f8ef1b210a481f1a6d6deaec0cbefe32585724c042719dcba9'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_construction_v1.json', 'bytes': 1850, 'sha256': '6f5ec778f4a4e6cca73b472f3e5d3f2a332075387f0760f53a68ef15a96bfb85'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_completion_v1.json', 'bytes': 246287, 'sha256': '935f92eebd048e7519a9f227bf6bd0434f21b7053a11b229464adac878fcc2eb'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_CUDA_request_v1.json', 'bytes': 29059, 'sha256': '0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b'}]), hashed_bytes=total)))