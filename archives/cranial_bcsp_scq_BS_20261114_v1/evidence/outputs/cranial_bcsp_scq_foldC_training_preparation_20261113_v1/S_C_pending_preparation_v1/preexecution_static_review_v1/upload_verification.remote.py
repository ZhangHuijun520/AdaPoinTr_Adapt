from pathlib import Path
import hashlib, json, tarfile, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_S_foldC_training_pending_20261113_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 21138 and h(p.read_bytes()) == 'c04bcbe09c46815540f9c7b4b4f093e4768c85a45588798fdc4ae8e407413d51'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'c04bcbe09c46815540f9c7b4b4f093e4768c85a45588798fdc4ae8e407413d51' and int(Path(str(p) + '.bytes').read_text()) == 21138
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 4 and len({m.name for m in ms}) == 4
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert set(expected) == {m.name for m in ms}
    assert h(t.extractfile('installation_mapping_S_C_v1.json').read()) == 'aec2ddd80fd1f8b65d1f19be203b4eceea9361ad7837e4a8bf59ab408f7663aa'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_AND_THREE_SIDECARS_PASS', members=4)))