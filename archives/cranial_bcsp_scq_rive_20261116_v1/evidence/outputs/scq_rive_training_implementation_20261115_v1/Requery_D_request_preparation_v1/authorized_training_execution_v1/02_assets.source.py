import pathlib, json, hashlib, tarfile, io, socket, os
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Requery_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    b = t.extractfile('installation_mapping_v1.json').read()
assert hashlib.sha256(b).hexdigest() == 'ee97d9473ffcfbd28a563d1638f76b5736eb96dcc48627bc7200b26c6b000e45'
m = json.loads(b)
rs = m['reused_readonly_records'] + [dict(path=r['target'], bytes=r['bytes'], sha256=r['sha256']) for r in m['files']]
assert len(rs) == 74
for r in rs:
    p = P(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == r['bytes']), str(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(1048576), b''):
            h.update(b)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='ALL74_BOUND_ASSETS_PASS', files=74)))
