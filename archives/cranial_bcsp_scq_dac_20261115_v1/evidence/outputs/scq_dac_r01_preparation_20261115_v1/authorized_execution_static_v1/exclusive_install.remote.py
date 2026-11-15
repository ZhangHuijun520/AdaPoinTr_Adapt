from pathlib import Path, PurePosixPath
import os, socket, json, tarfile, hashlib, time
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
P = Path('/home/jovyan/adapointr_work/PoinTr')
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')
p = Path('/home/jovyan/scq_dac_r1_frozen20_transport_20261115_v1.tar.gz')
T = time.monotonic()

def clean(x):
    x = Path(x)
    assert not any((y.is_symlink() for y in (x, *x.parents)))
    return x

def stream(f):
    h = hashlib.sha256()
    n = 0
    for b in iter(lambda : f.read(4194304), b''):
        n += len(b)
        h.update(b)
        assert time.monotonic() - T < 110
    return (n, h.hexdigest())
assert P.resolve() == P and clean(root.parent).is_dir() and os.access(root.parent, os.W_OK | os.X_OK)
for x in (root, out):
    assert not clean(x).exists()
assert clean(p).stat().st_size == 906620311
st = p.stat()
with p.open('rb') as f:
    assert stream(f)[1] == '350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01'
side = clean(str(p) + '.contents.sha256')
assert side.is_file()
catalog = {n: h for (h, n) in (line.split('  ', 1) for line in side.read_text().splitlines())}
assert len(catalog) == 30
rows = None
seen = set()
with tarfile.open(p, 'r|gz') as t:
    for m in t:
        assert m.isfile() and m.name in catalog and (m.name not in seen) and (not PurePosixPath(m.name).is_absolute()) and ('..' not in PurePosixPath(m.name).parts)
        if m.name == 'metadata/install_manifest_v1.json':
            b = t.extractfile(m).read()
            assert hashlib.sha256(b).hexdigest() == '3ad689a73763caa52805e69c60e923955cbbd42a8d20d4c34aaead81998cafa0'
            v = json.loads(b)
            assert v['request_sha256'] == '129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8' and v['root'] == str(root)
            rows = v['files']
            a = (len(b), hashlib.sha256(b).hexdigest())
        else:
            with t.extractfile(m) as f:
                a = stream(f)
        assert a == (m.size, catalog[m.name])
        seen.add(m.name)
assert len(seen) == 30 and len(rows) == 28 and (len({r['target'] for r in rows}) == 28)
for r in rows:
    target = clean(r['target'])
    assert str(target.relative_to(root)) == r['member'][8:] and r['member'].startswith('payload/') and (not target.exists())
assert (st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns) == (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
os.umask(63)
root.mkdir(mode=448)
for n in ('weights', 'replay', 'control'):
    (root / n).mkdir(mode=448)
written = []
with tarfile.open(p, 'r|gz') as t:
    bymember = {r['member']: r for r in rows}
    for m in t:
        if m.name not in bymember:
            continue
        r = bymember[m.name]
        target = clean(r['target'])
        assert not target.exists()
        with t.extractfile(m) as source, target.open('xb') as dest:
            while True:
                b = source.read(4194304)
                if not b:
                    break
                dest.write(b)
        with target.open('rb') as f:
            assert stream(f) == (r['bytes'], r['sha256'])
        written.append(r['target'])
assert len(written) == 28
print(json.dumps(dict(status='EXACT28_EXCLUSIVE_INSTALL_HASH_PASS', files=28, root=str(root), seconds=time.monotonic() - T)))