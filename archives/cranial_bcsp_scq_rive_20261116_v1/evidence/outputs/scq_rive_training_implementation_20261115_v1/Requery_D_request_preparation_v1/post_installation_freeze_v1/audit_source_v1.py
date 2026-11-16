import pathlib, json, hashlib, tarfile, io, os, socket, stat
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Requery_D_pending_20261115_v1.tar.gz')
assert not any((x.is_symlink() for x in (p, *p.parents)))
b = p.read_bytes()
assert len(b) == 12264 and hashlib.sha256(b).hexdigest() == 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    b = t.extractfile('installation_mapping_v1.json').read()
assert hashlib.sha256(b).hexdigest() == 'ee97d9473ffcfbd28a563d1638f76b5736eb96dcc48627bc7200b26c6b000e45'
m = json.loads(b)
assert len(m['files']) == 2
root = P(m['existing_install_root'])
assert root.is_dir() and (not any((x.is_symlink() for x in (root, *root.parents))))
rows = []
objects = {}
for r in m['files']:
    p = P(r['target'])
    s = p.lstat()
    assert p.parent == root and stat.S_ISREG(s.st_mode) and (s.st_uid == 1000) and (s.st_size == r['bytes'])
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    assert h == r['sha256']
    z = p.stat()
    assert all((getattr(s, k) == getattr(z, k) for k in ('st_ino', 'st_dev', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode', 'st_uid')))
    rows.append(dict(path=str(p), bytes=len(b), sha256=h, mode=oct(stat.S_IMODE(s.st_mode)), uid=s.st_uid))
    objects[r['role']] = json.loads(b)
q = objects['request']
a = objects['Static_D_formal_freeze']
assert q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
assert q['paired_baseline']['freeze']['sha256'] == rows[1]['sha256'] and a['status'] == 'FORMAL_RIVE_POST_TRAINING_FREEZE_AUDIT_PASS' and all(a['checks'].values())
for p in m['must_remain_absent']:
    assert not os.path.lexists(p), p
assert q['paired_baseline']['freeze'] == dict(path=m['files'][1]['target'], bytes=m['files'][1]['bytes'], sha256=m['files'][1]['sha256'])
assert a['arm'] == 'RF-Static' and a['fold'] == q['fold'] == 'D' and (a['identity'] == q['identity']) and (a['request_sha256'] == 'f2a9d28fae758c5e718c28bc463d9c90de8b07b752ec89d80441807827018fb2')
print(json.dumps(dict(status='TWOFILE_FORMAL_POST_INSTALLATION_AUDIT_PASS', files=rows, paired_freeze_bound=True, Requery_controls_output_absent=True, server_writes=0, root_listing=sorted((x.name for x in root.iterdir())))))
