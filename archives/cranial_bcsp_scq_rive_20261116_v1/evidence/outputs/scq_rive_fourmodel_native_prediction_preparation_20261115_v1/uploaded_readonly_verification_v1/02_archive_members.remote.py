import pathlib, json, hashlib, tarfile, io, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz')
b = p.read_bytes()
assert len(b) == 83164 and hashlib.sha256(b).hexdigest() == 'ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    ms = t.getmembers()
    assert len(ms) == len({x.name for x in ms}) == 16 and sum((x.size for x in ms)) <= 1048576
    data = {}
    for x in ms:
        n = pathlib.PurePosixPath(x.name)
        assert x.isfile() and (not n.is_absolute()) and ('..' not in n.parts)
        data[x.name] = t.extractfile(x).read()
        assert len(data[x.name]) == x.size
rows = [dict(member=n, bytes=len(v), sha256=hashlib.sha256(v).hexdigest()) for (n, v) in sorted(data.items())]
ct = ''.join((r['sha256'] + '  ' + r['member'] + '\n' for r in rows))
assert P(str(p) + '.contents.sha256').read_bytes() == ct.encode()
mb = data['installation_mapping_v1.json']
assert hashlib.sha256(mb).hexdigest() == 'c67690dc37f1b3d77a0822ac3069cb508cdca1b7c4bac536702a9aadbe383dd5'
m = json.loads(mb)
assert len(m['files']) == 15 and m['new_install_root'] is True
assert set(data) == {'installation_mapping_v1.json'} | {r['member'] for r in m['files']}
for r in m['files']:
    v = data[r['member']]
    assert len(v) == r['bytes'] and hashlib.sha256(v).hexdigest() == r['sha256'] and (r['overwrite'] is False) and (r['write_mode'] == 'exclusive_binary_create_xb')
    assert pathlib.PurePosixPath(r['target']).parent == pathlib.PurePosixPath(m['install_root'])
r = next((r for r in m['files'] if r['role'] == 'request'))
q = json.loads(data[r['member']])
assert r['sha256'] == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774' and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and (q['execution_authorized'] is False)
assert q['forward_budget'] == 420 and q['batch_size'] == 1 and (q['unique_cases'] == 210) and all((q[k] == 0 for k in ('loss_calls', 'backward', 'optimizer_steps', 'BNCal', 'warmup', 'TTA')))
for k in ('entry', 'input_index', 'protocol', 'P3', 'numeric_policy'):
    x = next((v for v in m['files'] if v['target'] == q[k]['path']))
    assert all((x[z] == q[k][z] for z in ('bytes', 'sha256')))
p3 = json.loads(data['payload/implementation_P3_v1.json'])
assert p3['status'] == 'LOCAL_RIVE_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256'] == q['entry']['sha256'] and all(p3['checks'].values())
print(json.dumps(dict(status='SIXTEEN_MEMBER_MAPPING_AND_PENDING_REQUEST_PASS', members=rows, request_sha256=r['sha256'], targets=15, reused_files=len(m['reused_readonly_records']), server_writes=0)))
