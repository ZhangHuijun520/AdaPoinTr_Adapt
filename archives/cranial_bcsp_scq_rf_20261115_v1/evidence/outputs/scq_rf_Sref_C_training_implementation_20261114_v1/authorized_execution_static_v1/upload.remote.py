from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_Sref_foldC_training_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 106555 and h(p.read_bytes()) == 'eb68d200627443e924ff6e14840fa340c5d1a576e9bb89f599d42f4456a3cc5c'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'eb68d200627443e924ff6e14840fa340c5d1a576e9bb89f599d42f4456a3cc5c' and int(Path(str(p) + '.bytes').read_text()) == 106555
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 16
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 16 and len({m.name for m in ms}) == 16 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == 'f2b46bc04d1baf3d0c5b75ff04197285be727852e5094cbdb33021078bdf6c5f'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=16)))