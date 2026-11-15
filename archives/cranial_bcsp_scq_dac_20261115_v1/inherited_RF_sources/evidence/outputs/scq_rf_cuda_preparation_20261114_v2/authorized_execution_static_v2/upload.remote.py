from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 44555 and h(p.read_bytes()) == 'e9247e6f213cb1060bf7dc5ce093b371cda6128419e005d201356753527c53f7'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == 'e9247e6f213cb1060bf7dc5ce093b371cda6128419e005d201356753527c53f7' and int(Path(str(p) + '.bytes').read_text()) == 44555
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 8
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 8 and len({m.name for m in ms}) == 8 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v2.json').read()) == 'c22a62c1e586533a641a94fae63b8c654bb03f234d374adb92cb7e417fa0e8b8'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=8)))