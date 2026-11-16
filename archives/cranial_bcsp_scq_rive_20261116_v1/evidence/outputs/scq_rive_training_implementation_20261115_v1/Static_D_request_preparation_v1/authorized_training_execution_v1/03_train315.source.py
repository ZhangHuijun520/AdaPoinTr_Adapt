import pathlib, json, hashlib, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Static_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2'
q = json.loads(b)
qc = q['QC']

def bound(r):
    p = P(r['path'])
    b = p.read_bytes()
    assert len(b) == r['bytes'] and hashlib.sha256(b).hexdigest() == r['sha256']
    return b
f = json.loads(bound(qc['fold_binding']))['folds']['D']
ids = f['train_case_ids']
assert len(ids) == len(set(ids)) == 315 and len(set(f['train_sources'])) == 63 and (not set(f['train_sources']) & set(f['dev_sources']))
idx = {r['case_id']: r for r in [json.loads(x) for x in bound(qc['manifests']['8192']).decode().splitlines()]}
total = 0
for cid in ids:
    r = idx[cid]
    rel = pathlib.PurePosixPath(r['point_path'])
    assert not rel.is_absolute() and '..' not in rel.parts and (r['source_id'] in f['train_sources'])
    p = P(q['data_root']) / rel
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
    s = p.stat()
    h = hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda : stream.read(1048576), b''):
            h.update(b)
            total += len(b)
    z = p.stat()
    assert (s.st_size, s.st_mtime_ns, s.st_ctime_ns) == (z.st_size, z.st_mtime_ns, z.st_ctime_ns) and h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='TRAIN315_HASHES_PASS', files=315, sources=63, hashed_bytes=total, array_loads=0, dev_payload_reads=0)))
