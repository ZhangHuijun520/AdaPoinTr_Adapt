from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 73519 and h(p.read_bytes()) == '62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0' and int(Path(str(p) + '.bytes').read_text()) == 73519
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == len(expected) == 15 and len({m.name for m in ms}) == 15
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == '52f9e6d197e977302ba1490b3a1b2d0f057b8e4806f30064dc142b9e998d998d'
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS', members=15)))