from pathlib import Path
import hashlib, json, tarfile, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_B_foldD_training_pending_20261113_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 16423 and h(p.read_bytes()) == '5950205c3719fb0f9bd12e65685099c93f87dd644c3b54ae26df6962994d242c'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '5950205c3719fb0f9bd12e65685099c93f87dd644c3b54ae26df6962994d242c' and int(Path(str(p) + '.bytes').read_text()) == 16423
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 5 and len({m.name for m in ms}) == 5
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert set(expected) == {m.name for m in ms}
    assert h(t.extractfile('installation_mapping_B_D_v1.json').read()) == '53dd9e8d8f07724d357bdff9258e91013fd9bea3a99feb0651e552dba8383c4e'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_AND_THREE_SIDECARS_PASS', members=5)))