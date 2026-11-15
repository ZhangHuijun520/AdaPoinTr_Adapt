from pathlib import Path
import hashlib, json, tarfile, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_artificial_cuda_pending_20261113_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 2581773 and h(p.read_bytes()) == 'd226d30d8b188bbfa457d2f100af22fb2a4f3d849e40d4e2136116e709b03cba'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'd226d30d8b188bbfa457d2f100af22fb2a4f3d849e40d4e2136116e709b03cba' and int(Path(str(p) + '.bytes').read_text()) == 2581773
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 10 and len({m.name for m in ms}) == 10
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert set(expected) == {m.name for m in ms}
    assert h(t.extractfile('installation_mapping_v1.json').read()) == '4ae1c3ebcd4651ba628cd1ad64a65c0f8bca7f8cf4719239f28ee5cfab346b2f'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_AND_THREE_SIDECARS_PASS', members=10)))