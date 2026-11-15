from pathlib import Path
import socket, hashlib, tarfile, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/bcsp_scq_rf_ten_memory_pending_20261114_v1.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '47ded0d089350fbbd5f00c2e8fdbcb0d19d563dd686fa4e626e7c93fae5b020a'
with tarfile.open(p) as t:
    index = json.loads(t.extractfile('payload/SCQ_RF_ten_memory_execution_request_v1.json').read())
records = {r['input']['path']: r['input'] for r in index['cases']}
assert len(index['cases']) == 10 and len(records) == 10
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
print(json.dumps(dict(status='ALL_TEN_INPUT_HASHES_PASS', files=10, occurrences=10, hashed_bytes=total, array_reads=0)))