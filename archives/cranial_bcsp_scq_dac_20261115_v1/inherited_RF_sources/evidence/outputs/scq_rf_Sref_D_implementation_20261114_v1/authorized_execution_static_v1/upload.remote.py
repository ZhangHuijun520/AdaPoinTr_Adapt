from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_Sref_D_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 36661 and h(p.read_bytes()) == '16c0f203c40cb9eba913e2546318a1a8f2cb6f2d23b0fa91e4f95167520117e4'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '16c0f203c40cb9eba913e2546318a1a8f2cb6f2d23b0fa91e4f95167520117e4' and int(Path(str(p) + '.bytes').read_text()) == 36661
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 12
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 12 and len({m.name for m in ms}) == 12 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == 'ccb90e987710139e92181238e85a89412333dda82ead99246af2675b31946777'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=12)))