from pathlib import Path
import json, tarfile, hashlib, socket, os
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1')
p = Path('/home/jovyan/bcsp_scq_artificial_cuda_pending_20261113_v1.tar.gz')
assert not root.exists() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'd226d30d8b188bbfa457d2f100af22fb2a4f3d849e40d4e2136116e709b03cba'
with tarfile.open(p) as t:
    raw = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(raw).hexdigest() == '4ae1c3ebcd4651ba628cd1ad64a65c0f8bca7f8cf4719239f28ee5cfab346b2f'
    m = json.loads(raw)
    rows = m['files']
    assert len(rows) == 9
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
print(json.dumps(dict(status='NINE_FILES_EXCLUSIVE_INSTALL_HASH_PASS', files=9)))