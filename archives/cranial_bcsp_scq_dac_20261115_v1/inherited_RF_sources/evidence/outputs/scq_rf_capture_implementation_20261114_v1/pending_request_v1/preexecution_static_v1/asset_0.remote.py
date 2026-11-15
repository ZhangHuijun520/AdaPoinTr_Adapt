from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/bcsp_scq_fourmodel_native_predict_v2.py', 'bytes': 37227, 'sha256': 'c74e0da099d170dca3f4d1e002998ad0ce634aae702f0d2e6b324cc469ef5d81'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_prediction_execution_request_v2.json', 'bytes': 17562, 'sha256': 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_mamba_encoder_v1.py', 'bytes': 3546, 'sha256': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_p1_model_factory_v1.py', 'bytes': 4396, 'sha256': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/bcsp_scq_fourmodel_native_predict_v2.py', 'bytes': 37227, 'sha256': 'c74e0da099d170dca3f4d1e002998ad0ce634aae702f0d2e6b324cc469ef5d81'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_prediction_execution_request_v2.json', 'bytes': 17562, 'sha256': 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_mamba_encoder_v1.py', 'bytes': 3546, 'sha256': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_p1_model_factory_v1.py', 'bytes': 4396, 'sha256': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4'}]), hashed_bytes=total)))