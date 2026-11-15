from pathlib import Path
import json, tarfile, hashlib, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_B_foldD_training_pending_20261113_v1.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '5950205c3719fb0f9bd12e65685099c93f87dd644c3b54ae26df6962994d242c'
with tarfile.open(p) as t:
    fold = json.loads(Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1' + '/fold_binding.json').read_bytes())['folds']['D']
    rows = [json.loads(s) for s in Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1' + '/manifest_8192.jsonl').read_text().splitlines()]
    records = {r['case_id']: r for r in rows}
    ids = fold['train_case_ids']
    sources = set(fold['train_sources'])
    assert len(rows) == len(records) == 420 and len(ids) == len(set(ids)) == 315 and (len(sources) == 63)
    root = Path('/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1')
    total = 0
    for cid in ids:
        r = records[cid]
        rel = Path(r['point_path'])
        assert not rel.is_absolute() and '..' not in rel.parts and (r['source_id'] in sources)
        f = root / rel
        assert f.is_file() and f.suffix == '.npz' and (not any((x.is_symlink() for x in (f, *f.parents))))
        h = hashlib.sha256()
        with f.open('rb') as stream:
            for b in iter(lambda : stream.read(1048576), b''):
                h.update(b)
                total += len(b)
        assert h.hexdigest() == r['sha256'], str(f)
print(json.dumps(dict(status='ALL315_TRAIN_PAYLOAD_HASHES_PASS', cases=315, sources=63, hashed_bytes=total, array_reads=0)))