from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 895438 and h(p.read_bytes()) == '1193e0fde217ffd4059c17272d194b022964e390f56c4d8d0b7ba53936edf7ce'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '1193e0fde217ffd4059c17272d194b022964e390f56c4d8d0b7ba53936edf7ce' and int(Path(str(p) + '.bytes').read_text()) == 895438
lines = Path(str(p) + '.contents.sha256').read_text().splitlines()
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in lines}
assert len(lines) == len(expected) == 13
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 13 and len({m.name for m in ms}) == 13 and (set(expected) == {m.name for m in ms})
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == 'd2c866ab983b24aaa7d71695ba9cc7d0e221f9a7f17387925966d80c9e9f170c'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_THREE_SIDECARS_PASS', members=13)))