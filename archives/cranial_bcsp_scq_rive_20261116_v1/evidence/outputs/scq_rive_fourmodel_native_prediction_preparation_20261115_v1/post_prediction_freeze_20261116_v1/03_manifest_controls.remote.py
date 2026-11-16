from pathlib import Path, PurePosixPath
import json, hashlib, os, socket, math, collections
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
b = (I / 'RIVE_fourmodel_native_prediction_execution_request_v1.json').read_bytes()
assert hashlib.sha256(b).hexdigest() == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q = json.loads(b)
idx = json.loads(Path(q['input_index']['path']).read_bytes())
rows = idx['inputs']
runs = idx['runs']
log = [json.loads(s) for s in (O / 'inference_manifest.jsonl').read_text().splitlines()]
claims = [json.loads(s) for s in (O / 'forward_attempts.jsonl').read_text().splitlines()]
assert len(rows) == len(log) == len(claims) == 420
counts = collections.Counter()
total = 0
for (i, (row, r, c)) in enumerate(zip(rows, log, claims), 1):
    assert r['forward_index'] == c['forward_index'] == i and c['status'] == 'CLAIMED_BEFORE_FORWARD'
    assert r['run'] == c['run'] == row['run'] and r['case_id'] == c['case_id'] == row['case_id']
    for k in ('variant', 'source_id', 'fold', 'n_input', 'n_output', 'normalization'):
        assert r[k] == row[k]
    run = next((x for x in runs if x['label'] == row['run']))
    assert r['input_sha256'] == row['input']['sha256'] and r['checkpoint_sha256'] == run['checkpoint']['sha256']
    p = O / row['prediction_filename']
    v = r['prediction']
    assert v['name'] == row['prediction_filename'] and p.stat().st_size == v['bytes'] and (hashlib.sha256(p.read_bytes()).hexdigest() == v['sha256'])
    assert math.isfinite(r['operational_seconds']) and r['operational_seconds'] >= 0
    total += v['bytes']
    counts[r['run']] += 1
assert dict(counts) == {r['label']: 105 for r in runs} and (not (O / 'cache_manifest.jsonl').read_bytes())
L = q['launch_contract']
a = json.loads(Path(L['authorization']).read_bytes())
rt = json.loads(Path(L['runtime']).read_bytes())
claim = json.loads(Path(q['launch_attempt']).read_bytes())
assert a['explicit_user_authorization'] is True and a['request_sha256'] == hashlib.sha256(b).hexdigest()
ah = hashlib.sha256(Path(L['authorization']).read_bytes()).hexdigest()
assert rt == dict(schema='bcsp-development-runtime-v1', request_sha256=a['request_sha256'], authorization_sha256=ah)
assert claim == dict(status='CLAIMED_BEFORE_TMUX', request_sha256=a['request_sha256'])
print(json.dumps(dict(status='ALL420_MANIFEST_CLAIM_AND_CONTROLS_PASS', counts=dict(counts), prediction_bytes=total, authorization=a, runtime=rt, claim=claim, cache_records=0, server_writes=0)))
