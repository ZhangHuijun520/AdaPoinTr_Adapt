from pathlib import Path, PurePosixPath
import socket, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'

def bound(r):
    p = Path(r['path'])
    assert p.stat().st_size == r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256']
    return p
fold = json.loads(bound({'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}).read_bytes())['folds']['D']
ids = fold['train_case_ids']
assert len(ids) == len(set(ids)) == 315
rows = {r['case_id']: r for r in [json.loads(l) for l in bound({'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}).read_text().splitlines()]}
root = Path('/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1')
total = 0
for cid in ids:
    r = rows[cid]
    relative = PurePosixPath(r['point_path'])
    assert not relative.is_absolute() and '..' not in relative.parts and (r['source_id'] in fold['train_sources'])
    p = root / r['point_path']
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
    before = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda : f.read(1048576), b''):
            h.update(chunk)
            total += len(chunk)
    after = p.stat()
    assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='TRAIN315_EXACT_HASHES_PASS', files=315, sources=63, hashed_bytes=total, array_reads=0)))