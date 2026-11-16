import pathlib, json, hashlib, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
expected = [('bcsp_rive_Requery_D_pending_20261115_v1.tar.gz', 12264, 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'), ('bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.bytes', 6, 'cf406ffc941753810c803c1851b802bee91a6a55dcdda43fd03c6ef0d7df5e1e'), ('bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.contents.sha256', 356, '913cf7d58b9877406d89b34915890b1175daf98209b79ff280e6c3c86366270b'), ('bcsp_rive_Requery_D_pending_20261115_v1.tar.gz.sha256', 113, 'b41f7335a345460e9209b5f3689b2680fe2d01e796f3548ed102988146cf3b93')]
rows = []
for (n, size, h) in expected:
    p = P('/home/jovyan') / n
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == size)
    b = p.read_bytes()
    assert hashlib.sha256(b).hexdigest() == h
    rows.append(dict(path=str(p), bytes=len(b), sha256=h))
print(json.dumps(dict(status='FOUR_UPLOADED_FILES_PASS', hostname=socket.gethostname(), uid=os.getuid(), files=rows, server_writes=0)))
