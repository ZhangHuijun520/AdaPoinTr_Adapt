from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v2')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v2')
archive = Path('/home/jovyan/bcsp_scq_rf_Static_D_selector_diag_pending_20261115_v2.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == '5647a26486caab0171d522c7decc9f1fedfec3ccf2ca3a956f000ba548b11380')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v2.json').read()
    assert hashlib.sha256(b).hexdigest() == '8e3e70395012fe466a3856bba91d0b9274c06c49de0dc1780bcd9074bb5e83dd'
    rows = json.loads(b)['files']
    assert len(rows) == 8
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
print(json.dumps(dict(status='EIGHT_FILES_EXCLUSIVE_INSTALL_PASS', files=8)))