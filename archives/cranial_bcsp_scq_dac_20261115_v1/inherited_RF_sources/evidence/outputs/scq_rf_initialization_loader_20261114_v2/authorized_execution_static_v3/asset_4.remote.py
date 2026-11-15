from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/bcsp_lqi_twofold_native_predict_v1.py', 'bytes': 31207, 'sha256': 'b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_p1_training_runtime_v1.py', 'bytes': 11268, 'sha256': '939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_mamba_encoder_v1.py', 'bytes': 3546, 'sha256': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_p1_model_factory_v1.py', 'bytes': 4396, 'sha256': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/bcsp_lqi_twofold_native_predict_v1.py', 'bytes': 31207, 'sha256': 'b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_p1_training_runtime_v1.py', 'bytes': 11268, 'sha256': '939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_mamba_encoder_v1.py', 'bytes': 3546, 'sha256': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_p1_model_factory_v1.py', 'bytes': 4396, 'sha256': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4'}]), hashed_bytes=total)))