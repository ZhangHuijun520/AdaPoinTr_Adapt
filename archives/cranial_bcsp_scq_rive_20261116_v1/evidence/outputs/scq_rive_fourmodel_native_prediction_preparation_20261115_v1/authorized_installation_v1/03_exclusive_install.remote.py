import pathlib, json, hashlib, tarfile, io, os, socket
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
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    assert len(t.getmembers()) == 16
    data = {r['member']: t.extractfile(r['member']).read() for r in m['files']}
root = P(m['install_root'])
assert m['new_install_root'] is True and (not os.path.lexists(root)) and root.parent.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
assert len(m['files']) == len({r['target'] for r in m['files']}) == 15
for r in m['files']:
    p = P(r['target'])
    assert p.parent == root and (not os.path.lexists(p)) and (r['overwrite'] is False) and (r['write_mode'] == 'exclusive_binary_create_xb')
    v = data[r['member']]
    assert len(v) == r['bytes'] and hashlib.sha256(v).hexdigest() == r['sha256']
for x in m['must_remain_absent']:
    assert not os.path.lexists(x), x
written = []
created = False
try:
    root.mkdir(mode=448)
    created = True
    for r in m['files']:
        p = P(r['target'])
        with p.open('xb') as f:
            f.write(data[r['member']])
            f.flush()
            os.fsync(f.fileno())
        written.append(str(p))
        print(json.dumps(dict(status='EXCLUSIVE_WRITE', path=str(p))), flush=True)
    assert {x.name for x in root.iterdir()} == {P(r['target']).name for r in m['files']}
    rows = []
    for r in m['files']:
        p = P(r['target'])
        assert p.is_file() and (not p.is_symlink()) and (p.stat().st_size == r['bytes']) and (hashlib.sha256(p.read_bytes()).hexdigest() == r['sha256'])
        rows.append(dict(path=str(p), bytes=r['bytes'], sha256=r['sha256']))
    for x in m['must_remain_absent']:
        assert not os.path.lexists(x), x
    print(json.dumps(dict(status='FIFTEEN_FILES_ONE_DIRECTORY_INSTALL_READBACK_PASS', files=rows, new_directory=str(root), tests=0, prediction=0, training=0)))
except BaseException as e:
    print(json.dumps(dict(status='FAILED_STOP_NO_RETRY', written=written, root_created=created, error=repr(e))), flush=True)
    raise
