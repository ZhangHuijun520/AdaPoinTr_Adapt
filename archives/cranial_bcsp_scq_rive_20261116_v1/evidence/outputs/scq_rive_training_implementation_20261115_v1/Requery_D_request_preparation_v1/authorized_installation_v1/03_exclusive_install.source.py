import pathlib, json, hashlib, tarfile, io, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Requery_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
assert len(b) == 12264 and hashlib.sha256(b).hexdigest() == 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    mb = t.extractfile('installation_mapping_v1.json').read()
    assert hashlib.sha256(mb).hexdigest() == 'ee97d9473ffcfbd28a563d1638f76b5736eb96dcc48627bc7200b26c6b000e45'
    m = json.loads(mb)
    assert len(m['files']) == 2
    data = {r['member']: t.extractfile(r['member']).read() for r in m['files']}
root = P(m['existing_install_root'])
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
for r in m['files']:
    p = P(r['target'])
    assert p.parent == root and (not os.path.lexists(p)) and (r['overwrite'] is False)
    v = data[r['member']]
    assert len(v) == r['bytes'] and hashlib.sha256(v).hexdigest() == r['sha256']
for x in m['must_remain_absent']:
    assert not os.path.lexists(x), x
names = {x.name for x in root.iterdir()}
written = []
try:
    for r in m['files']:
        p = P(r['target'])
        with p.open('xb') as f:
            f.write(data[r['member']])
            f.flush()
            os.fsync(f.fileno())
        written.append(str(p))
        print(json.dumps(dict(status='EXCLUSIVE_WRITE', path=str(p))), flush=True)
    assert {x.name for x in root.iterdir()} == names | {P(r['target']).name for r in m['files']}
    rows = []
    for r in m['files']:
        p = P(r['target'])
        assert p.is_file() and (not p.is_symlink()) and (p.stat().st_size == r['bytes']) and (hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'])
        rows.append(dict(path=str(p), bytes=r['bytes'], sha256=r['sha256']))
    for x in m['must_remain_absent']:
        assert not os.path.lexists(x), x
    print(json.dumps(dict(status='TWO_FILE_INSTALL_READBACK_PASS', files=rows, tests=0, training=0)))
except BaseException as e:
    print(json.dumps(dict(status='FAILED_STOP_NO_RETRY', written=written, error=repr(e))), flush=True)
    raise
