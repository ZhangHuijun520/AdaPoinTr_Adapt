from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_Static_C_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 30797 and h(p.read_bytes()) == 'a8ead5604eeb733e2cc78a0f1448e3e21fe55a915b441c01ced541a9aa16b342'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'a8ead5604eeb733e2cc78a0f1448e3e21fe55a915b441c01ced541a9aa16b342' and int(Path(str(p) + '.bytes').read_text()) == 30797
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 9
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 9 and len({m.name for m in ms}) == 9 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == '987597524287f8e3d437d8d6c086063c6a4ae8530ce62621c9adba1338685a9c'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=9)))