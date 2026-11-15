from pathlib import Path
import json, tarfile, hashlib, socket, os
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1')
p = Path('/home/jovyan/bcsp_scq_B_foldC_training_pending_20261113_v1.tar.gz')
assert not root.exists() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert hashlib.sha256(p.read_bytes()).hexdigest() == '11844500cc5ad90c69941090943c18c043d141e149cf95158276e7be68abfa93'
with tarfile.open(p) as t:
    raw = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(raw).hexdigest() == '87f0d513d56619c018d68635937c61c7e86bd6ae5d5976470dbeb208527b8997'
    m = json.loads(raw)
    rows = m['files']
    assert len(rows) == 24
    for r in rows:
        target = Path(r['target'])
        assert target.parent == root and (not target.exists()) and (not target.is_symlink())
        data = t.extractfile(r['member']).read()
        assert len(data) == r['bytes'] and hashlib.sha256(data).hexdigest() == r['sha256']
    root.mkdir(mode=448)
    for r in rows:
        target = Path(r['target'])
        data = t.extractfile(r['member']).read()
        with target.open('xb') as f:
            f.write(data)
        assert target.stat().st_size == r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256']
    (root / 'control').mkdir(mode=448)
print(json.dumps(dict(status='TWENTY_FOUR_FILES_EXCLUSIVE_INSTALL_HASH_PASS', files=24)))