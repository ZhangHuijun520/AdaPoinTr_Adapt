from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'RIVE_fourmodel_native_prediction_execution_request_v1.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q = json.loads(qp.read_bytes())
c = json.loads((O / 'completion.json').read_bytes())
a = c['archive']
p = O / 'development_predictions_v1.tar.gz'
assert c['status'] == 'PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT' and c['forwards'] == 420 and (c['request_sha256'] == hashlib.sha256(qp.read_bytes()).hexdigest())
h = hashlib.sha256()
with p.open('rb') as f:
    for b in iter(lambda : f.read(1048576), b''):
        h.update(b)
assert a['path'] == str(p) and a['bytes'] == p.stat().st_size and (a['sha256'] == h.hexdigest())
expected = {'.bytes': str(a['bytes']) + '\n', '.sha256': a['sha256'] + '  ' + p.name + '\n', '.contents.sha256': ''.join((r['sha256'] + '  ' + r['name'] + '\n' for r in a['members']))}
rows = [dict(path=str(p), bytes=a['bytes'], sha256=a['sha256'])]
for (suf, text) in expected.items():
    x = Path(str(p) + suf)
    b = x.read_bytes()
    assert b == text.encode()
    rows.append(dict(path=str(x), bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
assert sum((x.stat().st_size for x in O.rglob('*') if x.is_file())) <= q['limits']['output_bytes']
print(json.dumps(dict(status='ARCHIVE_AND_THREE_SIDECARS_PASS', files=rows, archive_members=len(a['members']), server_writes=0)))
