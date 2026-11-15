from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/bcsp_scq_rf_sixmodel_native_pending_20261115_v1.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 98016 and h(p.read_bytes()) == '552d439ddd85293d66c6b9c632fbb4110a68dc6d60b7452eb705e991946640ca'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '552d439ddd85293d66c6b9c632fbb4110a68dc6d60b7452eb705e991946640ca' and int(Path(str(p) + '.bytes').read_text()) == 98016
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == len(expected) == 17 and len({m.name for m in ms}) == 17
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v1.json').read()) == '8acb68fe59be381b3488c32000dadec5ff851e72ffd2ec33f3171a0a0f9c67a0'
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS', members=17)))