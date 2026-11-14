from pathlib import Path
import hashlib, json, tarfile, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_S_foldD_training_pending_20261113_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 22101 and h(p.read_bytes()) == 'd370c964b8e785de1a6d57e2ff1836ac3479876a4ad1de8c5ee6fb37bdde3b89'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'd370c964b8e785de1a6d57e2ff1836ac3479876a4ad1de8c5ee6fb37bdde3b89' and int(Path(str(p) + '.bytes').read_text()) == 22101
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 4 and len({m.name for m in ms}) == 4
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert set(expected) == {m.name for m in ms}
    assert h(t.extractfile('installation_mapping_S_D_v1.json').read()) == '4abdf739cbd55fa26ca2d5a8e9ae2a33bfe93df585a6673260c3dc474a41ec40'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_AND_THREE_SIDECARS_PASS', members=4)))