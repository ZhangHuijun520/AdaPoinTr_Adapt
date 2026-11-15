from pathlib import Path
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
total = 0
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v2/ckpt-last.pth', 'bytes': 489927058, 'sha256': 'c2acf8d8f8587db465e0f46dacb14cc25f10a585c3573ff7521c8eceb75bab93'}]:
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
print(json.dumps(dict(status='EXACT_HASHES_PASS', files=len([{'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v2/ckpt-last.pth', 'bytes': 489927058, 'sha256': 'c2acf8d8f8587db465e0f46dacb14cc25f10a585c3573ff7521c8eceb75bab93'}]), hashed_bytes=total)))