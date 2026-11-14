from pathlib import Path
import socket, os, tarfile, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v1.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0'
with tarfile.open(p) as t:
    index = json.loads(t.extractfile('payload/SCQ_BS_CD_input_index_v1.json').read())
roots = [Path('/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points'), Path('/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points')]
for r in roots:
    assert r.is_dir() and (not any((x.is_symlink() for x in (r, *r.parents))))
rows = {r['case_id']: r for r in index['inputs']}
assert len(rows) == 210
results = []
total = 0
for (cid, row) in rows.items():
    assert Path(cid).name == cid and '..' not in cid
    options = []
    for root in roots:
        f = root / (cid + '_8192.npz')
        r = dict(path=str(f), exists=f.exists())
        assert not any((x.is_symlink() for x in (f, *f.parents))), str(f)
        if f.exists():
            assert f.is_file()
            before = f.stat()
            h = hashlib.sha256()
            with f.open('rb') as stream:
                for b in iter(lambda : stream.read(1048576), b''):
                    h.update(b)
                    total += len(b)
            after = f.stat()
            assert (before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            r.update(bytes=before.st_size, sha256=h.hexdigest(), exact=before.st_size == row['input']['bytes'] and h.hexdigest() == row['input']['sha256'])
        options.append(r)
    matches = [r for r in options if r.get('exact')]
    preferred = [r for r in matches if r['path'] == row['input']['path']]
    selected = (preferred or matches)[0] if matches else None
    results.append(dict(case_id=cid, fold=row['fold'], expected=row['input'], candidates=options, selected=selected))
ok = all((r['selected'] is not None for r in results))
print(json.dumps(dict(status='ALL210_EXACT_PATHS_RESOLVED' if ok else 'INPUTS_MISSING_OR_MISMATCHED_STOP', hostname=socket.gethostname(), rows=results, unique_cases=210, candidate_paths=420, hashed_bytes=total, array_reads=0, server_writes=0, selection_rule='Prefer original candidate if exact; otherwise the other of two frozen roots; no substitution of hash or case.')))