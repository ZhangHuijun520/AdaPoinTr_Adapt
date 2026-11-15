from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_Requery_D_pending_20261115_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 39971 and h(p.read_bytes()) == '9b44bd1edf2de96e180942d7fb421b2c8a468e35b7bfb1c384c6a71a36b76f75'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '9b44bd1edf2de96e180942d7fb421b2c8a468e35b7bfb1c384c6a71a36b76f75' and int(Path(str(p) + '.bytes').read_text()) == 39971
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 11
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 11 and len({m.name for m in ms}) == 11 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == '7199a6923144bff79d8c6063893137ee477f404962c042b189dcdc11531be442'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=11)))