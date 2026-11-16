import pathlib, json, hashlib, os, socket
P = pathlib.Path
p = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json')
b = p.read_bytes()
assert hashlib.sha256(b).hexdigest() == 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'
q = json.loads(b)
I = q['identity']
assert socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] == 1000
records = [q['implementation'][k] for k in ['encoder', 'factory', 'lqi_decoder', 'lqi_factory', 'scq_residual', 'scq_factory', 'rf_residual', 'rf_factory', 'timezone', 'cuda_entry']] + q['dependencies'] + [q[k] for k in ('initialization', 'rf_initialization', 'static_config', 'preflight_scope')] + [q['QC']['fold_binding'], q['QC']['manifests']['8192'], q['implementation']['preflight_helper']]
records.append({'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'})

def read(r):
    p = P(r['path'])
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))), str(p)
    s = p.stat()
    assert s.st_size == r['bytes'], str(p)
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(1048576), b''):
            h.update(b)
    assert h.hexdigest() == r['sha256'], str(p)
    return p
scope = json.loads(read(q['preflight_scope']).read_bytes())
S = scope['bindings']
rs = {r['relative_target']: r for r in S['candidate']}
rs.update({r['relative_path']: r for r in S['isolated_model_project_sources']})
assert len(rs) == 18
for (rel, r) in rs.items():
    records.append(dict(path=str(P(q['model_root']) / rel), bytes=r['bytes'], sha256=r['sha256']))
records.append(dict(S['base_config'], path=str(P(q['model_root']) / 'base_model.yaml')))
records += S['provider'] + S['environment_metadata']
unique = {}
for r in records:
    if r['path'] in unique:
        assert unique[r['path']] == {k: r[k] for k in ('path', 'bytes', 'sha256')}
    unique[r['path']] = {k: r[k] for k in ('path', 'bytes', 'sha256')}
assert len(unique) <= 96 and sum((r['bytes'] for r in unique.values())) <= 1073741824
for r in unique.values():
    read(r)
a = json.loads(P({'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/RF_CUDA_freeze_audit_v3.json', 'bytes': 26364, 'sha256': '7611114686154f2024c1489e5d5cb64f59201dd27b112c0e18614c1ca25f1c0e'}['path']).read_bytes())
assert a['status'] == 'FORMAL_RF_POST_CUDA_FREEZE_AUDIT_PASS' and all(a['checks'].values())
print(json.dumps(dict(status='NECESSARY_FROZEN_ASSETS_PASS', files=list(unique.values()), total_bytes=sum((r['bytes'] for r in unique.values())), server_writes=0)))
