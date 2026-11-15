from pathlib import Path
import socket, os, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v1')
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v1.tar.gz')
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(p.read_bytes()).hexdigest() == '62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0')
with tarfile.open(p) as t:
    data = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(data).hexdigest() == '52f9e6d197e977302ba1490b3a1b2d0f057b8e4806f30064dc142b9e998d998d'
    m = json.loads(data)
    rows = m['files']
    assert len(rows) == 14
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
print(json.dumps(dict(status='FOURTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=14)))