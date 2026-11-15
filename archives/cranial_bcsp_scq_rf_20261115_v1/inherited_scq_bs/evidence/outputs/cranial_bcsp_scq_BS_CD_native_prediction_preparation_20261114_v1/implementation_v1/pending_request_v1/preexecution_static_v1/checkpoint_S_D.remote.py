from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldD_seed0_train_20261113_v1/ckpt-last.pth', 'bytes': 487148386, 'sha256': 'bd8fe23f1a276019b776b5d2cadce7aad62bd31eea440975ffd1222331f636fa'}]:
    p = Path(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
    assert p.stat().st_size == r['bytes']
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(4194304), b''):
            h.update(b)
            total += len(b)
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldD_seed0_train_20261113_v1/ckpt-last.pth', 'bytes': 487148386, 'sha256': 'bd8fe23f1a276019b776b5d2cadce7aad62bd31eea440975ffd1222331f636fa'}]), hashed_bytes=total)))