from pathlib import Path
import json, tarfile, hashlib, socket, os
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1')
p = Path('/home/jovyan/bcsp_scq_B_foldC_UTC_order_pending_20261113_v2.tar.gz')
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert not (root / 'control_v2').exists() and (not (root / 'control_v2').is_symlink())
assert hashlib.sha256(p.read_bytes()).hexdigest() == '865d9f36185b348c9886a5d268c4fb197d859182e156dd44e4ee0a05e4cbfe98'
with tarfile.open(p) as t:
    raw = t.extractfile('installation_mapping_v2.json').read()
    assert hashlib.sha256(raw).hexdigest() == '080cfe3b45fc7b4125395ec236e703406c5cd5526965e4db0328a2f3b592236c'
    m = json.loads(raw)
    rows = m['files']
    assert len(rows) == 5
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
    (root / 'control_v2').mkdir(mode=448)
print(json.dumps(dict(status='FIVE_V2_FILES_EXCLUSIVE_INSTALL_HASH_PASS', files=5)))