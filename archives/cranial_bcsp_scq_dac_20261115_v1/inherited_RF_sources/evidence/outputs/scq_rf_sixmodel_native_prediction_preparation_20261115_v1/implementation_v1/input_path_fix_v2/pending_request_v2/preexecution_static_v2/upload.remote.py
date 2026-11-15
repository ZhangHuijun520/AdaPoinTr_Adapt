from pathlib import Path
import hashlib, tarfile, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/bcsp_scq_rf_sixmodel_native_pending_20261115_v2.tar.gz')
assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents))))
h = lambda b: hashlib.sha256(b).hexdigest()
assert p.stat().st_size == 111177 and h(p.read_bytes()) == '73220c29b29977e429da66b8a010fa6e796754aafecc898602c287eecafa2ff1'
for s in ['.sha256', '.bytes', '.contents.sha256']:
    assert Path(str(p) + s).is_file() and (not Path(str(p) + s).is_symlink())
assert Path(str(p) + '.sha256').read_text().split()[0] == '73220c29b29977e429da66b8a010fa6e796754aafecc898602c287eecafa2ff1' and int(Path(str(p) + '.bytes').read_text()) == 111177
expected = {l.split(None, 1)[1]: l.split(None, 1)[0] for l in Path(str(p) + '.contents.sha256').read_text().splitlines()}
with tarfile.open(p) as t:
    ms = t.getmembers()
    assert len(ms) == len(expected) == 21 and len({m.name for m in ms}) == 21
    for m in ms:
        assert m.isfile() and (not m.name.startswith('/')) and ('..' not in Path(m.name).parts) and (m.size < 4194304)
        assert m.name in expected and h(t.extractfile(m).read()) == expected[m.name]
    assert h(t.extractfile('installation_mapping_v2.json').read()) == '1136795eb60becddfc3181fea49ba259c9f70e8218852f19be9007d9a2241e2f'
print(json.dumps(dict(status='UPLOAD_AND_THREE_SIDECARS_PASS', members=21)))