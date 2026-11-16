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
rs = m['reused_readonly_records']
assert len(rs) == 55 and sum((r['bytes'] for r in rs)) <= 1073741824
for r in rs:
    p = P(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == r['bytes']), str(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for v in iter(lambda : f.read(1048576), b''):
            h.update(v)
    assert h.hexdigest() == r['sha256'], str(p)
root = P(m['install_root'])
assert not os.path.lexists(root) and root.parent.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
for r in m['files']:
    assert not os.path.lexists(r['target']), r['target']
print(json.dumps(dict(status='ALL55_REUSED_FILES_PASS', files=55, new_targets_absent=True, server_writes=0)))
