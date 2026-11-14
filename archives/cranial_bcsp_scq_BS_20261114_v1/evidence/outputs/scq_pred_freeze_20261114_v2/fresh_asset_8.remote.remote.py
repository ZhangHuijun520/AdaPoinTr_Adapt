from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json', 'bytes': 23220, 'sha256': 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/__init__.py', 'bytes': 264, 'sha256': '6d3fee6ff8e8ec4dcab0f7af6c7890ff81f3d9319707865f5a651239aee9ae0a'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json', 'bytes': 23220, 'sha256': 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/mamba_ssm/__init__.py', 'bytes': 264, 'sha256': '6d3fee6ff8e8ec4dcab0f7af6c7890ff81f3d9319707865f5a651239aee9ae0a'}]), hashed_bytes=total)))