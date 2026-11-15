from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v1')
archive = Path('/home/jovyan/bcsp_scq_rf_Static_D_pending_20261115_v1.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == '0190144483093af5b876a0fc3ed61e6fdfa514bf2ef9cd1041a7c8a80fe86d00')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(b).hexdigest() == '2ca37ee5b51bdebf43fd84614754bbd4ecf9ee5b7e9c1365c5d108a4981b5379'
    rows = json.loads(b)['files']
    assert len(rows) == 13
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
print(json.dumps(dict(status='THIRTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=13)))