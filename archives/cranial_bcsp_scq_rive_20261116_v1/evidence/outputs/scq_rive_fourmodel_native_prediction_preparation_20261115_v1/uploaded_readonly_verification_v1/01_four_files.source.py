import pathlib, json, hashlib, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
expected = [('bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz', 83164, 'ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef'), ('bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.bytes', 6, '699eb981f54a3063c5dce106763a90c60252c74c400496878e2e08f2f9e6243d'), ('bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.contents.sha256', 1731, 'de1b0a199b9523cd5d7df7214bf978870034e3e7ca5e77726b0f9b9ae6858728'), ('bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz.sha256', 120, '525a7ba37a51fcecff22d31cf5c63b67c598b6a0ca638242d78e60a9c8bc6709')]
rows = []
for (n, size, h) in expected:
    p = P('/home/jovyan') / n
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == size), str(p)
    b = p.read_bytes()
    assert hashlib.sha256(b).hexdigest() == h, str(p)
    rows.append(dict(path=str(p), bytes=len(b), sha256=h))
print(json.dumps(dict(status='FOUR_UPLOADED_FILES_PASS', hostname=socket.gethostname(), uid=os.getuid(), files=rows, server_writes=0)))
