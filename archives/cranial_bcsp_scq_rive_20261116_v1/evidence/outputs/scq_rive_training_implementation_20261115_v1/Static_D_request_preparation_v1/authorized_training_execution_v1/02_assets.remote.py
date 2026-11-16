import pathlib, json, hashlib, tarfile, io, socket, os
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Static_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == '1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    b = t.extractfile('installation_mapping_v1.json').read()
assert hashlib.sha256(b).hexdigest() == 'f20428fad63d08e8483c07be97ed2a733b1986b50a48feee5a6d56af42e78272'
m = json.loads(b)
rs = m['reused_readonly_records'] + [dict(path=r['target'], bytes=r['bytes'], sha256=r['sha256']) for r in m['files']]
assert len(rs) == 72
for r in rs:
    p = P(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == r['bytes']), str(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(1048576), b''):
            h.update(b)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='ALL72_BOUND_ASSETS_PASS', files=72)))
