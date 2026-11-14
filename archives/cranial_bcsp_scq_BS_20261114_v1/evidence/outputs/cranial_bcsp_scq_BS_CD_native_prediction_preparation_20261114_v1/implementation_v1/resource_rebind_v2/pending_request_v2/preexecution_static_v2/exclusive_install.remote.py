from pathlib import Path
import socket, os, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2')
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v2.tar.gz')
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(p.read_bytes()).hexdigest() == '5f1330046c557551fb6ca5af130b30386d37d643dcc10bfc7b1c162dad2bae06')
with tarfile.open(p) as t:
    data = t.extractfile('installation_mapping_v2.json').read()
    assert hashlib.sha256(data).hexdigest() == '8b0700baba3f2b7aabd79d70d974342fcf0c9ce992787b3c0d026cd0f27fd3e1'
    m = json.loads(data)
    rows = m['files']
    assert len(rows) == 18
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
print(json.dumps(dict(status='EIGHTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=18)))