from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/bcsp_scq_rf_Static_D_selector_diag_pending_20261115_v2.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 36900 and h(p.read_bytes()) == '5647a26486caab0171d522c7decc9f1fedfec3ccf2ca3a956f000ba548b11380'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '5647a26486caab0171d522c7decc9f1fedfec3ccf2ca3a956f000ba548b11380' and int(Path(str(p) + '.bytes').read_text()) == 36900
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 9
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 9 and len({m.name for m in ms}) == 9 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v2.json').read()) == '8e3e70395012fe466a3856bba91d0b9274c06c49de0dc1780bcd9074bb5e83dd'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=9)))