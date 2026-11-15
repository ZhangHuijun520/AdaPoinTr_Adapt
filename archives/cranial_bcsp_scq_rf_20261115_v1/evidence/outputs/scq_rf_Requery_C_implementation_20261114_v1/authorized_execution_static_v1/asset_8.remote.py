from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_training_contract_01dt08_v3.py', 'bytes': 16531, 'sha256': '08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/inherited_training_budget_v1.py', 'bytes': 20395, 'sha256': '095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/bcsp_lqi_twofold_native_predict_v1.py', 'bytes': 31207, 'sha256': 'b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309'}]:
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
print(json.dumps(dict(status='EXACT_REUSED_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_training_contract_01dt08_v3.py', 'bytes': 16531, 'sha256': '08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/inherited_training_budget_v1.py', 'bytes': 20395, 'sha256': '095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/bcsp_lqi_twofold_native_predict_v1.py', 'bytes': 31207, 'sha256': 'b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309'}]), hashed_bytes=total)))