import pathlib, json, hashlib, os, socket
P = pathlib.Path
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'
q = json.loads(b)
I = q['identity']
assert socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] == 1000
records = [{'label': 'Static_C', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldC_seed0_train_20261115_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': '80c59d40fe3d0a415e41c67f1b036f619e2e862fde829f42a66ecb73e950eb97'}, {'label': 'Requery_C', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': '5fc095755fa22fec79230394f3d3cd5dc461fd18e4ff1e366e52e5ae033dc87e'}, {'label': 'Static_D', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Static_foldD_seed0_train_20261115_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': 'f196f5b1bf406e4018baf11ae5d977dc445f515ea4b72aff431a061e64740b45'}, {'label': 'Requery_D', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/ckpt-last.pth', 'bytes': 489927058, 'sha256': 'e2528ee8a65f3c8a1a44798a89af1d47a94c3a02aa2c0de2a48ed6bf1a880533'}]
total = 0
rows = []
for r in records:
    p = P(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
    s = p.stat()
    assert s.st_size == r['bytes'] and s.st_size <= 600000000
    total += s.st_size
    assert total <= 2400000000
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(1048576), b''):
            h.update(b)
    z = p.stat()
    assert (s.st_size, s.st_mtime_ns, s.st_ctime_ns) == (z.st_size, z.st_mtime_ns, z.st_ctime_ns) and h.hexdigest() == r['sha256'], str(p)
    rows.append(r)
print(json.dumps(dict(status='FOUR_FROZEN_CHECKPOINTS_PASS', files=rows, total_bytes=total, checkpoint_loads=0, server_writes=0)))
