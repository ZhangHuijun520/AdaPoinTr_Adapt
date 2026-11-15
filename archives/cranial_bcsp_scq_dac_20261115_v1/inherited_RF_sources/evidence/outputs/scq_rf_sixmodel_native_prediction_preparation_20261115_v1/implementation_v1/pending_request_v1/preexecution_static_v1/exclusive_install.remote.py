from pathlib import Path
import socket, os, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v1')
p = Path('/home/jovyan/bcsp_scq_rf_sixmodel_native_pending_20261115_v1.tar.gz')
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(p.read_bytes()).hexdigest() == '552d439ddd85293d66c6b9c632fbb4110a68dc6d60b7452eb705e991946640ca')
with tarfile.open(p) as t:
    data = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(data).hexdigest() == '8acb68fe59be381b3488c32000dadec5ff851e72ffd2ec33f3171a0a0f9c67a0'
    m = json.loads(data)
    rows = m['files']
    assert len(rows) == 16
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
print(json.dumps(dict(status='SIXTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=16)))