from pathlib import Path
import socket, os, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1')
p = Path('/home/jovyan/bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz')
for x in [root, out]:
    assert not x.exists() and (not any((z.is_symlink() for z in (x, *x.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(p.read_bytes()).hexdigest() == '47ded0d089350fbbd5f00c2e8fdbcb0d19d563dd686fa4e626e7c93fae5b020a')
with tarfile.open(p) as t:
    data = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(data).hexdigest() == 'fbcb206798bf7c51206295e31f1f887e246f810b809cddc6a5045ac6244cac95'
    m = json.loads(data)
    rows = m['files']
    assert len(rows) == 17
    for r in rows:
        target = Path(r['target'])
        assert target.parent in [root, root / 'references'] and (not target.exists()) and (not target.is_symlink())
        b = t.extractfile(r['member']).read()
        assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    root.mkdir(mode=448)
    (root / 'references').mkdir(mode=448)
    for r in rows:
        target = Path(r['target'])
        b = t.extractfile(r['member']).read()
        with target.open('xb') as f:
            f.write(b)
        assert target.stat().st_size == r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256']
    (root / 'control').mkdir(mode=448)
print(json.dumps(dict(status='SEVENTEEN_FILES_EXCLUSIVE_INSTALL_PASS', files=17)))