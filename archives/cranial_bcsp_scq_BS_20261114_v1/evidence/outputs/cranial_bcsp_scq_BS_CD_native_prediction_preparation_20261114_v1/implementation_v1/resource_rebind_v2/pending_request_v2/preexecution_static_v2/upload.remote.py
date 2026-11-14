from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v2.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 79701 and h(p.read_bytes()) == '5f1330046c557551fb6ca5af130b30386d37d643dcc10bfc7b1c162dad2bae06'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '5f1330046c557551fb6ca5af130b30386d37d643dcc10bfc7b1c162dad2bae06' and int(Path(str(p) + '.bytes').read_text()) == 79701
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == len(expected) == 19 and len({m.name for m in ms}) == 19
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v2.json').read()) == '8b0700baba3f2b7aabd79d70d974342fcf0c9ce992787b3c0d026cd0f27fd3e1'
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS', members=19)))