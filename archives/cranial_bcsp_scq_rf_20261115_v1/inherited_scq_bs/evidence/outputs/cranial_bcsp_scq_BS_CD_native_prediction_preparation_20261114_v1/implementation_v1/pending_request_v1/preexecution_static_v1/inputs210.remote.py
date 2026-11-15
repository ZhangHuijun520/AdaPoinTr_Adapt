from pathlib import Path
import socket, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/bcsp_scq_BS_CD_native_prediction_pending_20261114_v1.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '62299acb5258e340ac2c2b2abc44fa3c1d112a87efe963abacf89f47c2951cf0'
with tarfile.open(p) as t:
    index = json.loads(t.extractfile('payload/SCQ_BS_CD_input_index_v1.json').read())
records = {r['input']['path']: r['input'] for r in index['inputs']}
assert len(index['inputs']) == 420 and len(records) == 210
total = 0
for r in records.values():
    p = Path(r['path'])
    assert p.suffix == '.npz' and p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == r['bytes'])
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(1048576), b''):
            h.update(b)
            total += len(b)
    assert h.hexdigest() == r['sha256'], str(p)
print(json.dumps(dict(status='ALL210_INPUT_HASHES_PASS', files=210, occurrences=420, hashed_bytes=total, array_reads=0)))