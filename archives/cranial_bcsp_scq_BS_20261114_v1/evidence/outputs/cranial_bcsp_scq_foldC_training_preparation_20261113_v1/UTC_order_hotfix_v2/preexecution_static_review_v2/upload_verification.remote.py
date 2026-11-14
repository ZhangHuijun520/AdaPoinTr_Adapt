from pathlib import Path
import hashlib, json, tarfile, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_B_foldC_UTC_order_pending_20261113_v2.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 17284 and h(p.read_bytes()) == '865d9f36185b348c9886a5d268c4fb197d859182e156dd44e4ee0a05e4cbfe98'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '865d9f36185b348c9886a5d268c4fb197d859182e156dd44e4ee0a05e4cbfe98' and int(Path(str(p) + '.bytes').read_text()) == 17284
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == 6 and len({m.name for m in ms}) == 6
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert set(expected) == {m.name for m in ms}
    assert h(t.extractfile('installation_mapping_v2.json').read()) == '080cfe3b45fc7b4125395ec236e703406c5cd5526965e4db0328a2f3b592236c'
print(json.dumps(dict(status='UPLOAD_ARCHIVE_AND_THREE_SIDECARS_PASS', members=6)))