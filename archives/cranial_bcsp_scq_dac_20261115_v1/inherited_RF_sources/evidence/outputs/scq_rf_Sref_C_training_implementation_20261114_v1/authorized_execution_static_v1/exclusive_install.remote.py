from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v1')
archive = Path('/home/jovyan/bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == 'eb68d200627443e924ff6e14840fa340c5d1a576e9bb89f599d42f4456a3cc5c')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(b).hexdigest() == 'f2b46bc04d1baf3d0c5b75ff04197285be727852e5094cbdb33021078bdf6c5f'
    rows = json.loads(b)['files']
    assert len(rows) == 15
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
print(json.dumps(dict(status='FIFTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=15)))