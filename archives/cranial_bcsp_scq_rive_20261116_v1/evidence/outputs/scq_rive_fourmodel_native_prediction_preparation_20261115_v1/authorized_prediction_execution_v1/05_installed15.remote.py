import pathlib, json, hashlib, tarfile, io, os, socket, stat
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz')
assert not any((x.is_symlink() for x in (p, *p.parents)))
b = p.read_bytes()
assert len(b) == 83164 and hashlib.sha256(b).hexdigest() == 'ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    mb = t.extractfile('installation_mapping_v1.json').read()
assert hashlib.sha256(mb).hexdigest() == 'c67690dc37f1b3d77a0822ac3069cb508cdca1b7c4bac536702a9aadbe383dd5'
m = json.loads(mb)
root = P(m['install_root'])
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert len(m['files']) == 15 and {x.name for x in root.iterdir()} == {P(r['target']).name for r in m['files']}
rows = []
objects = {}
keys = ('st_ino', 'st_dev', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid')
for r in m['files']:
    p = P(r['target'])
    s = p.lstat()
    assert p.parent == root and stat.S_ISREG(s.st_mode) and (s.st_uid == 1000) and (s.st_size == r['bytes'])
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    assert h == r['sha256'], str(p)
    z = p.lstat()
    assert all((getattr(s, k) == getattr(z, k) for k in keys)), str(p)
    rows.append(dict(path=str(p), bytes=len(b), sha256=h, uid=s.st_uid, mode=oct(stat.S_IMODE(s.st_mode)), fingerprint=[getattr(z, k) for k in keys]))
    if p.suffix == '.json':
        objects[r['role']] = json.loads(b)
q = objects['request']
p3 = objects['P3']
index = objects['input_index']
protocol = objects['protocol']
assert q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False and (q['forward_budget'] == 420) and (q['unique_cases'] == 210)
assert p3['status'] == 'LOCAL_RIVE_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256'] == q['entry']['sha256'] and all(p3['checks'].values())
for k in ('entry', 'input_index', 'protocol', 'P3', 'numeric_policy'):
    r = next((r for r in rows if r['path'] == q[k]['path']))
    assert r['bytes'] == q[k]['bytes'] and r['sha256'] == q[k]['sha256']
assert [r['label'] for r in index['runs']] == ['Static_C', 'Requery_C', 'Static_D', 'Requery_D'] and len(index['inputs']) == 420 and (len({r['input']['path'] for r in index['inputs']}) == 210)
assert protocol['inference']['forward_attempt_budget'] == protocol['outputs']['predictions'] == 420
for x in m['must_remain_absent']:
    assert not os.path.lexists(x), x
print(json.dumps(dict(status='FORMAL_FIFTEEN_FILE_POST_INSTALLATION_AUDIT_PASS', files=rows, request_pending=True, exact_names=True, execution_paths_absent=m['must_remain_absent'], directories=[], server_writes=0, tests=0, forward=0)))
