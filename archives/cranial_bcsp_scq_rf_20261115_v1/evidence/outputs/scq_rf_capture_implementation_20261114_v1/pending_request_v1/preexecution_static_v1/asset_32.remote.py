from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_S_C_training_audit_v1.json', 'bytes': 14132, 'sha256': 'fac7dd65d7a1bf1dc351b453b8c48d3a688263675f7a80ae6cb5e479b83f0523'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_B_D_training_audit_v1.json', 'bytes': 14981, 'sha256': 'b90b89f4dab2e176cb986efde2433d98e1c7d176d9e0e7a74e370c5c6e612753'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_S_D_training_audit_v1.json', 'bytes': 16792, 'sha256': '0e65d9b88fd26350b6a444f8fc225be805c390459f4312ff10dd57e1b02aa89b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_S_C_training_audit_v1.json', 'bytes': 14132, 'sha256': 'fac7dd65d7a1bf1dc351b453b8c48d3a688263675f7a80ae6cb5e479b83f0523'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_B_D_training_audit_v1.json', 'bytes': 14981, 'sha256': 'b90b89f4dab2e176cb986efde2433d98e1c7d176d9e0e7a74e370c5c6e612753'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/frozen_S_D_training_audit_v1.json', 'bytes': 16792, 'sha256': '0e65d9b88fd26350b6a444f8fc225be805c390459f4312ff10dd57e1b02aa89b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}]), hashed_bytes=total)))