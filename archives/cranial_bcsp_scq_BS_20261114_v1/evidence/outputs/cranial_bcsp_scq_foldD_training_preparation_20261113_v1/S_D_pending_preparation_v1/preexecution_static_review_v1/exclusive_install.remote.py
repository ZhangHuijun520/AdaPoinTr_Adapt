from pathlib import Path
import json, tarfile, hashlib, socket, os
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1')
p = Path('/home/jovyan/bcsp_scq_S_foldD_training_pending_20261113_v1.tar.gz')
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert not (root / 'control_S_D_v1').exists() and (not (root / 'control_S_D_v1').is_symlink())
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd370c964b8e785de1a6d57e2ff1836ac3479876a4ad1de8c5ee6fb37bdde3b89'
with tarfile.open(p) as t:
    raw = t.extractfile('installation_mapping_S_D_v1.json').read()
    assert hashlib.sha256(raw).hexdigest() == '4abdf739cbd55fa26ca2d5a8e9ae2a33bfe93df585a6673260c3dc474a41ec40'
    m = json.loads(raw)
    rows = m['files']
    assert len(rows) == 3
    for r in rows:
        target = Path(r['target'])
        assert target.parent == root and (not target.exists()) and (not target.is_symlink())
        data = t.extractfile(r['member']).read()
        assert len(data) == r['bytes'] and hashlib.sha256(data).hexdigest() == r['sha256']
    for r in rows:
        target = Path(r['target'])
        data = t.extractfile(r['member']).read()
        with target.open('xb') as f:
            f.write(data)
        assert target.stat().st_size == r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256']
    (root / 'control_S_D_v1').mkdir(mode=448)
print(json.dumps(dict(status='THREE_SD_FILES_EXCLUSIVE_INSTALL_HASH_PASS', files=3)))