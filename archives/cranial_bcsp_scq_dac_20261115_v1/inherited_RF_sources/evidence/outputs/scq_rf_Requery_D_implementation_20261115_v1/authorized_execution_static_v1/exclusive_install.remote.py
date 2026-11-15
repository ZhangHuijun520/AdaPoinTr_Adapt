from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Requery_foldD_seed0_train_20261115_v1')
archive = Path('/home/jovyan/bcsp_scq_rf_Requery_D_pending_20261115_v1.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == '9b44bd1edf2de96e180942d7fb421b2c8a468e35b7bfb1c384c6a71a36b76f75')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(b).hexdigest() == '7199a6923144bff79d8c6063893137ee477f404962c042b189dcdc11531be442'
    rows = json.loads(b)['files']
    assert len(rows) == 10
    for r in rows:
        p = Path(r['target'])
        assert p.parent == root and (not p.exists()) and (not p.is_symlink())
        b = t.extractfile(r['member']).read()
        assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    root.mkdir(mode=448)
    for r in rows:
        p = Path(r['target'])
        b = t.extractfile(r['member']).read()
        with p.open('xb') as f:
            f.write(b)
        assert p.stat().st_size == r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
    (root / 'control').mkdir(mode=448)
print(json.dumps(dict(status='TEN_FILES_EXCLUSIVE_INSTALL_PASS', files=10)))