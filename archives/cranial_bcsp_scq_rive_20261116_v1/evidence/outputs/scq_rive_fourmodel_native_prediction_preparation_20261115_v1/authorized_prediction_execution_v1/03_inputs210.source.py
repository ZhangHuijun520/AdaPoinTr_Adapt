import pathlib, json, hashlib, os, socket
P = pathlib.Path
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'
q = json.loads(b)
I = q['identity']
assert socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] == 1000

def read(r):
    p = P(r['path'])
    b = p.read_bytes()
    assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    return b
folds = json.loads(read(q['QC']['fold_binding']))['folds']
manifest = {r['case_id']: r for r in [json.loads(s) for s in read(q['QC']['manifests']['8192']).decode().splitlines()]}
roots = {'C': '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points', 'D': '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points'}
rows = []
total = 0
for fold in 'CD':
    f = folds[fold]
    assert len(f['dev_case_ids']) == 105 and len(set(f['dev_sources'])) == 21 and (not set(f['train_sources']) & set(f['dev_sources']))
    for cid in f['dev_case_ids']:
        r = manifest[cid]
        assert r['source_id'] in f['dev_sources']
        p = P(roots[fold]) / (cid + '_8192.npz')
        assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
        s = p.stat()
        assert 0 < s.st_size <= 1048576
        total += s.st_size
        assert total <= 67108864
        h = hashlib.sha256()
        with p.open('rb') as stream:
            for b in iter(lambda : stream.read(1048576), b''):
                h.update(b)
        z = p.stat()
        assert (s.st_size, s.st_mtime_ns, s.st_ctime_ns) == (z.st_size, z.st_mtime_ns, z.st_ctime_ns) and h.hexdigest() == r['sha256'], str(p)
        rows.append(dict(fold=fold, case_id=cid, path=str(p), bytes=s.st_size, sha256=h.hexdigest()))
assert len(rows) == len({r['path'] for r in rows}) == 210
print(json.dumps(dict(status='ALL210_DEVELOPMENT_INPUT_HASHES_PASS', files=rows, total_bytes=total, array_loads=0, server_writes=0)))
