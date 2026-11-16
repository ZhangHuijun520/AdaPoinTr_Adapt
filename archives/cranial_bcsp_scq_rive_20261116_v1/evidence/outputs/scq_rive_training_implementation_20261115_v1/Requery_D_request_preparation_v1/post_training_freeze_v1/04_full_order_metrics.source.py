import pathlib, json, hashlib, math, collections, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
run = 'SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1'
q = json.loads((P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1') / (run + '_execution_request_v1.json')).read_bytes())
out = P(q['output'])
b = (out / 'order_plan.json').read_bytes()
assert hashlib.sha256(b).hexdigest() == q['order_plan']['sha256']
plan = json.loads(b)
f = json.loads(P(q['QC']['fold_binding']['path']).read_bytes())['folds']['D']
ids = set(f['train_case_ids'])
assert len(ids) == 315 and len(set(f['train_sources'])) == 63 and (not set(f['train_sources']) & set(f['dev_sources']))
index = {r['case_id']: r for r in [json.loads(s) for s in P(q['QC']['manifests']['8192']['path']).read_text().splitlines()]}
case = collections.Counter()
source = collections.Counter()
drop = collections.Counter()
step = 0
with (out / 'metrics.jsonl').open() as stream:
    for (epoch, e) in enumerate(plan['epochs']):
        assert e['epoch'] == epoch and len(e['batches']) == 39 and (len(e['dropped']) == 3)
        flat = [x for batch in e['batches'] for x in batch]
        assert len(flat) == len(set(flat)) == 312 and set(flat).isdisjoint(e['dropped']) and (set(flat + e['dropped']) == ids)
        drop.update(e['dropped'])
        for (batch, expected) in enumerate(e['batches']):
            r = json.loads(stream.readline())
            step += 1
            assert (r['step'], r['epoch'], r['batch']) == (step, epoch, batch) and r['case_ids'] == expected and (len(expected) == 8)
            ss = [index[x]['source_id'] for x in expected]
            assert r['source_ids'] == ss and set(ss) <= set(f['train_sources'])
            lr = 0.0001 * max(0.9 ** (epoch / 21), 0.02)
            bn = max(0.9 * 0.5 ** (epoch / 21), 0.01)
            assert len(r['LR']) == 2 and all((math.isclose(v, lr, rel_tol=1e-12) for v in r['LR'])) and math.isclose(r['BN_momentum'], bn, rel_tol=1e-12)
            assert r['optimizer_step_committed'] is True and r['clip_max_norm'] == 10 and (r['loss_denoise'] == r['loss_sparse'] == 0)
            assert all((math.isfinite(r[k]) for k in ('loss', 'loss_dense', 'loss_reconstruction', 'grad_norm_before_clip'))) and r['loss'] == r['loss_reconstruction'] == r['loss_dense']
            case.update(expected)
            source.update(ss)
    assert stream.read() == ''
a = json.loads((out / 'exposure.json').read_bytes())
h = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
assert step == 3900 and len(plan['epochs']) == 100 and (sum(case.values()) == sum(source.values()) == 31200) and (sum(drop.values()) == 300)
assert a == dict(case=dict(case), source=dict(source), dropped_case=dict(drop), order_sha256=h)
print(json.dumps(dict(status='ALL3900_BATCHES_SCHEDULES_EXPOSURES_PASS', updates=step, traversals=100, exposures=31200, drops=300, order_sha256=h, source_count=len(source))))
