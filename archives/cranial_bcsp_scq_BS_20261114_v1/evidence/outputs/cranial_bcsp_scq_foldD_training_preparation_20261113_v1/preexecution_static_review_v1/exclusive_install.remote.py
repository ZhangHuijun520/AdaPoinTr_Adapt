from pathlib import Path
import json, tarfile, hashlib, socket, os
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1')
p = Path('/home/jovyan/bcsp_scq_B_foldD_training_pending_20261113_v1.tar.gz')
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert not (root / 'control_B_D_v1').exists() and (not (root / 'control_B_D_v1').is_symlink())
assert hashlib.sha256(p.read_bytes()).hexdigest() == '5950205c3719fb0f9bd12e65685099c93f87dd644c3b54ae26df6962994d242c'
with tarfile.open(p) as t:
    raw = t.extractfile('installation_mapping_B_D_v1.json').read()
    assert hashlib.sha256(raw).hexdigest() == '53dd9e8d8f07724d357bdff9258e91013fd9bea3a99feb0651e552dba8383c4e'
    m = json.loads(raw)
    rows = m['files']
    assert len(rows) == 4
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
    (root / 'control_B_D_v1').mkdir(mode=448)
print(json.dumps(dict(status='FOUR_BD_FILES_EXCLUSIVE_INSTALL_HASH_PASS', files=4)))