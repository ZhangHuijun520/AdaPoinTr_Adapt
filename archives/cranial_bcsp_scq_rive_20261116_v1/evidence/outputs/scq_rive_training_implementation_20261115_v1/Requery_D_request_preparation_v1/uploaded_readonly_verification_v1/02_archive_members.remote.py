import pathlib, json, hashlib, tarfile, io, socket, os
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Requery_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
assert len(b) == 12264 and hashlib.sha256(b).hexdigest() == 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    ms = t.getmembers()
    assert len(ms) == len({m.name for m in ms}) == 3 and sum((m.size for m in ms)) <= 65536
    data = {}
    for m in ms:
        n = pathlib.PurePosixPath(m.name)
        assert m.isfile() and (not n.is_absolute()) and ('..' not in n.parts)
        data[m.name] = t.extractfile(m).read()
        assert len(data[m.name]) == m.size
rows = [dict(member=n, bytes=len(v), sha256=hashlib.sha256(v).hexdigest()) for (n, v) in sorted(data.items())]
contents = ''.join((r['sha256'] + '  ' + r['member'] + '\n' for r in rows))
assert P(str(p) + '.contents.sha256').read_text() == contents
mb = data['installation_mapping_v1.json']
assert hashlib.sha256(mb).hexdigest() == 'ee97d9473ffcfbd28a563d1638f76b5736eb96dcc48627bc7200b26c6b000e45'
m = json.loads(mb)
assert len(m['files']) == 2
for r in m['files']:
    v = data[r['member']]
    assert len(v) == r['bytes'] and hashlib.sha256(v).hexdigest() == r['sha256'] and (r['overwrite'] is False)
qr = next((r for r in m['files'] if r['role'] == 'request'))
q = json.loads(data[qr['member']])
assert q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
fr = next((r for r in m['files'] if r['role'] == 'Static_D_formal_freeze'))
assert q['paired_baseline']['freeze']['sha256'] == fr['sha256']
print(json.dumps(dict(status='THREE_MEMBER_MAPPING_PASS', members=rows, request_sha256=qr['sha256'], freeze_sha256=fr['sha256'], server_writes=0)))
assert q['paired_baseline']['freeze']==dict(path=fr['target'],bytes=fr['bytes'],sha256=fr['sha256'])
a=json.loads(data[fr['member']]);assert a['status']=='FORMAL_RIVE_POST_TRAINING_FREEZE_AUDIT_PASS' and a['fold']=='D' and a['arm']=='RF-Static' and all(a['checks'].values())
