from pathlib import Path
import socket, hashlib, tarfile, os, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2')
archive = Path('/home/jovyan/bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz')
for p in [root, out]:
    assert not p.exists() and (not any((x.is_symlink() for x in (p, *p.parents))))
assert root.parent.is_dir() and out.parent.is_dir() and (hashlib.sha256(archive.read_bytes()).hexdigest() == 'e9247e6f213cb1060bf7dc5ce093b371cda6128419e005d201356753527c53f7')
with tarfile.open(archive) as t:
    b = t.extractfile('installation_mapping_v2.json').read()
    assert hashlib.sha256(b).hexdigest() == 'c22a62c1e586533a641a94fae63b8c654bb03f234d374adb92cb7e417fa0e8b8'
    rows = json.loads(b)['files']
    assert len(rows) == 7
    for r in rows:
        p = Path(r['target'])
        assert p.parent == root and (not p.exists()) and (not p.is_symlink())
        b = t.extractfile(r['member']).read()
        assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    root.mkdir(mode=448)
    for r in rows:
        p = Path(r['target'])
        b = t.extractfile(r['member']).read()
        with p.open('xb') as f:
            f.write(b)
        assert p.stat().st_size == r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
    (root / 'control').mkdir(mode=448)
print(json.dumps(dict(status='SEVEN_FILES_EXCLUSIVE_INSTALL_PASS', files=7)))