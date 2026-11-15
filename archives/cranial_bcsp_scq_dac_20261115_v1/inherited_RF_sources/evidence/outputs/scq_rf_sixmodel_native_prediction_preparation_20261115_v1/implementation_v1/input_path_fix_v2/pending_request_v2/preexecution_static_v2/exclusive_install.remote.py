from pathlib import Path
import socket, os, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v2')
p = Path('/home/jovyan/bcsp_scq_rf_sixmodel_native_pending_20261115_v2.tar.gz')
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(p.read_bytes()).hexdigest() == '73220c29b29977e429da66b8a010fa6e796754aafecc898602c287eecafa2ff1')
with tarfile.open(p) as t:
    data = t.extractfile('installation_mapping_v2.json').read()
    assert hashlib.sha256(data).hexdigest() == '1136795eb60becddfc3181fea49ba259c9f70e8218852f19be9007d9a2241e2f'
    m = json.loads(data)
    rows = m['files']
    assert len(rows) == 20
    for r in rows:
        target = Path(r['target'])
        assert target.parent == root and (not target.exists()) and (not target.is_symlink())
        b = t.extractfile(r['member']).read()
        assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    root.mkdir(mode=448)
    for r in rows:
        target = Path(r['target'])
        b = t.extractfile(r['member']).read()
        with target.open('xb') as f:
            f.write(b)
        assert target.stat().st_size == r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256']
    (root / 'control').mkdir(mode=448)
print(json.dumps(dict(status='TWENTY_FILES_EXCLUSIVE_INSTALL_PASS', files=20)))