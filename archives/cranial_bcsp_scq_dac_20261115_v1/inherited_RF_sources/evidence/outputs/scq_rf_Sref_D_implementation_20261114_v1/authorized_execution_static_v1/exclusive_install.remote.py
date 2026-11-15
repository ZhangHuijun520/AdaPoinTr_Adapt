from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldD_seed0_train_20261114_v1')
archive = Path('/home/jovyan/bcsp_scq_rf_Sref_D_pending_20261114_v1.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == '16c0f203c40cb9eba913e2546318a1a8f2cb6f2d23b0fa91e4f95167520117e4')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(b).hexdigest() == 'ccb90e987710139e92181238e85a89412333dda82ead99246af2675b31946777'
    rows = json.loads(b)['files']
    assert len(rows) == 11
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
print(json.dumps(dict(status='ELEVEN_FILES_EXCLUSIVE_INSTALL_PASS', files=11)))