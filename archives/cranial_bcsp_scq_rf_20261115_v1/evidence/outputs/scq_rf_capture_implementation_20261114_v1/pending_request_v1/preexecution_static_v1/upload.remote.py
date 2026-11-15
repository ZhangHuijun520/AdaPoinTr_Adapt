from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 1021245 and h(p.read_bytes()) == '47ded0d089350fbbd5f00c2e8fdbcb0d19d563dd686fa4e626e7c93fae5b020a'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '47ded0d089350fbbd5f00c2e8fdbcb0d19d563dd686fa4e626e7c93fae5b020a' and int(Path(str(p) + '.bytes').read_text()) == 1021245
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == len(expected) == 18 and len({m.name for m in ms}) == 18
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == 'fbcb206798bf7c51206295e31f1f887e246f810b809cddc6a5045ac6244cac95'
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS', members=18)))