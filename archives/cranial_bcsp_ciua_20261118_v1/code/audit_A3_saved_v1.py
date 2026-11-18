"""Verify frozen A3 evidence and recompute saved-output metrics without model calls."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'A3_results_v1'
SHA = '27ed889122d260a2b24a4f85ff9bde3c1ca2e0e5d449e2b0e050982c94019b0b'


def load(path):
    return json.loads(Path(path).read_bytes())


def fingerprint(path):
    path = Path(path)
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), path
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4194304), b''):
            digest.update(block)
    return path.stat().st_size, digest.hexdigest()


def verify(record, path=None):
    assert fingerprint(path or record['path']) == (record['bytes'], record['sha256']), record


def jsonl(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def describe(points, center):
    points = points.astype(np.float64)
    centroid = points.mean(0)
    radius = np.sqrt(np.square(points - centroid).sum(1).mean())
    octants = (points >= center).astype(int) @ [1, 2, 4]
    return centroid, np.log(radius), np.bincount(octants, minlength=8) / len(points)


def main():
    request = ROOT / 'CIUA_A3_CPU_shadow_execution_request_v1.json'
    assert fingerprint(request)[1] == SHA
    q = load(request)
    assert q['mode'] == 'shadow' and q['counts'] == dict(cases=40, head_calls=120, encoder=0, dense=0, backward=0, step=0)
    controls = {k: Path(q['launch_contract'][k]) for k in ('authorization', 'runtime', 'launcher', 'exit_code', 'stdout', 'stderr')}
    material = load(ROOT / 'execution_materialization_receipt_v1.json')
    for name in ('authorization', 'runtime', 'launcher'):
        assert fingerprint(controls[name])[1] == material[name + '_sha256']
    auth = load(controls['authorization'])
    assert auth['request_sha256'] == material['request_sha256'] == SHA and auth['explicit_user_authorization'] is True
    assert load(controls['runtime']) == dict(schema='ciua-runtime-v1', request_sha256=SHA, authorization_sha256=material['authorization_sha256'])
    status = load(controls['exit_code'])
    assert status['exit_code'] == 0 and status['timed_out'] is False and status['request_sha256'] == SHA
    assert Path(q['attempt_claim']).read_text().strip() == SHA
    assert all(fingerprint(controls[k])[0] == 0 for k in ('stdout', 'stderr'))
    for record in [q[k] for k in ('entry', 'head_source', 'reuse_manifest', 'trace_archive', 'parent_analysis_request', 'parent_analysis_freeze', 'protocol', 'implementation_scope', 'P3', 'CPU_python')] + list(q['implementation'].values()) + list(q['checkpoints'].values()) + [p['metadata'] for p in q['packages'].values()]:
        verify(record)
    parent = load(q['parent_analysis_request']['path'])
    index = {(r['run'], r['case_id']): r for r in parent['rows']}
    a2 = load(q['parent_analysis_freeze']['path'])
    assert a2['status'] == 'CIUA_CPU_ANALYSIS_FORMAL_READ_ONLY_FREEZE_PASS' and all(a2['checks'].values())
    reuse = load(q['reuse_manifest']['path'])['records']
    pairs = [(r['run'], r['case_id']) for r in reuse]
    assert len(pairs) == len(set(pairs)) == 40 and all(sum(run == fold for run, _ in pairs) == 20 for fold in ('G2_C', 'G2_D'))
    expected = {'analysis': '', 'archive': 'ciua_results_v1.tar.gz'}
    archive = OUT / expected['archive']
    files = {f'features/{run}__{case}_NMR.npz' for run, case in pairs} | {'attempts.jsonl', 'completion.json', 'resources.jsonl', 'shadow_responses.json', 'stages.jsonl'}
    manifest = load(OUT / 'output_manifest.json')
    assert manifest['request_sha256'] == SHA and len(manifest['files']) == 45
    assert {Path(r['path']).as_posix() for r in manifest['files']} == files
    expected_disk = files | {'output_manifest.json', 'archive_receipt.json'} | {archive.name + s for s in ('', '.bytes', '.sha256', '.contents.sha256')}
    assert {p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()} == expected_disk
    assert [p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_dir()] == ['features']
    inventory = {name: fingerprint(OUT / name) for name in sorted(expected_disk)}
    for record in manifest['files']:
        assert inventory[Path(record['path']).as_posix()] == (record['bytes'], record['sha256'])
    receipt = load(OUT / 'archive_receipt.json')
    verify(receipt, archive)
    assert int(Path(str(archive)+'.bytes').read_text()) == receipt['bytes']
    assert Path(str(archive)+'.sha256').read_text().split() == [receipt['sha256'], archive.name]
    assert Path(str(archive)+'.contents.sha256').read_text().splitlines() == [f"{m['sha256']}  {m['name']}" for m in receipt['members']]
    wanted = {m['name']: m for m in receipt['members']}
    assert len(wanted) == len(receipt['members']) == 46 and wanted.keys() == files | {'output_manifest.json'}
    with tarfile.open(archive, 'r:gz') as stream:
        members = stream.getmembers()
        assert len(members) == 46 and {m.name for m in members} == wanted.keys()
        for member in members:
            record = wanted[member.name]
            assert member.isfile() and member.size == record['bytes']
            assert hashlib.sha256(stream.extractfile(member).read()).hexdigest() == record['sha256']
            assert inventory[member.name] == (record['bytes'], record['sha256'])
    assert jsonl(OUT / 'stages.jsonl') == [dict(stage='authorized_and_claimed', mode='shadow')]
    events = []
    for i, (run, case) in enumerate(pairs):
        for j, arm in enumerate('NMR', 1):
            for state in ('CLAIMED_BEFORE_HEAD', 'HEAD_RETURNED'):
                events.append(dict(run=run, case_id=case, arm=arm, status=state, total_claimed=i*3+j))
    assert jsonl(OUT / 'attempts.jsonl') == events
    res = jsonl(OUT / 'resources.jsonl')
    assert [(r['phase'], r['count']) for r in res] == [(phase, 3*(i+offset)) for i in range(40) for phase, offset in [('before_shadow', 0), ('after_shadow', 1)]] + [('before_manifest', 120)]
    for r in res:
        assert all(0 <= r['values'][key] <= q['limits'][key] for key in q['limits'])
        assert r['checks'] == dict(RSS=True, output=True, wall=True)
    assert sum(size for size, _ in inventory.values()) <= q['limits']['output_bytes']
    assert load(OUT / 'completion.json') == dict(status='CIUA_SHADOW120_COMPLETE_PENDING_FREEZE', head_calls=120, encoder=0, dense=0)
    summaries = load(OUT / 'shadow_responses.json')
    assert [(r['run'], r['case_id']) for r in summaries] == pairs
    case_rows = []
    with tarfile.open(q['trace_archive']['path'], 'r:gz') as trace:
        for r, saved in zip(reuse, summaries):
            run, case = r['run'], r['case_id']
            src = index[run, case]
            verify(src['input'])
            norm = q['normalizations'][run+'__'+case]
            assert norm == src['normalization'] and src['role'] == 'development' and src['input']['sha256'] == r['input_sha256']
            assert q['checkpoints'][run]['sha256'] == r['checkpoint_sha256']
            member = trace.getmember(r['member'])
            assert member.isfile() and member.size == r['trace']['bytes'] <= 2097152
            raw = trace.extractfile(member).read()
            assert hashlib.sha256(raw).hexdigest() == r['trace']['sha256']
            with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                original, x = z['Q'], z['x']
            with np.load(src['input']['path'], allow_pickle=False) as z:
                D = z['partial']
            assert D.shape == (8192,3) and D.dtype == np.float32 and np.isfinite(D).all()
            center = (D.min(0).astype(np.float64)+D.max(0).astype(np.float64))/2
            with np.load(OUT/f'features/{run}__{case}_NMR.npz', allow_pickle=False) as z:
                assert sorted(z.files) == list('MNR')
                outputs = {arm: z[arm] for arm in 'NMR'}
            assert all(v.shape == (256,3) and v.dtype == np.float32 and np.isfinite(v).all() for v in [original, *outputs.values()])
            assert x.shape == (256,1416) and x.dtype == np.float32 and np.isfinite(x).all()
            scale = norm['scale']
            replay = float(np.abs(outputs['N'].astype(np.float64)-original).max()*scale)
            assert np.allclose(outputs['N'], original, rtol=2e-5, atol=2e-6) and replay <= .01
            f = x[:,1024:1408]
            perturbations = {'N':f, 'M':np.broadcast_to(f.astype(np.float64).mean(0).astype(np.float32), f.shape), 'R':np.roll(f,-1,axis=0)}
            c0, r0, o0 = describe(outputs['N'], center)
            measures = {}
            for arm, points in outputs.items():
                delta = np.linalg.norm((points-outputs['N']).astype(np.float64),axis=1)*scale
                values = dict(mean_mm=float(delta.mean()),median_mm=float(np.median(delta)),p95_mm=float(np.quantile(delta,.95)),max_mm=float(delta.max()),f_delta_mean=float(np.linalg.norm((perturbations[arm]-f).astype(np.float64),axis=1).mean()))
                assert values.keys() == saved['responses'][arm].keys() and all(abs(v-saved['responses'][arm][k]) <= 1e-10 for k,v in values.items())
                centroid, radius, octants = describe(points, center)
                measures[arm] = dict(**values, centroid_shift_mm=float(np.linalg.norm(centroid-c0)*scale), signed_log_radius_change=float(radius-r0), octant_TV=float(.5*np.abs(octants-o0).sum()))
            case_rows.append(dict(run=run, case_id=case, source_id=r['source_id'], replay_max_component_mm=replay, arms=measures))
    aggregates = {}
    for label in ('G2_C','G2_D','all'):
        selected = [r for r in case_rows if label == 'all' or r['run'] == label]
        aggregates[label] = {}
        for arm in 'MR':
            aggregates[label][arm] = {}
            for key in selected[0]['arms'][arm]:
                values = np.array([r['arms'][arm][key] for r in selected])
                aggregates[label][arm][key] = dict(mean=float(values.mean()),median=float(np.median(values)),min=float(values.min()),max=float(values.max()))
    assert all(fingerprint(OUT / key) == value for key, value in inventory.items())
    assert 'torch' not in __import__('sys').modules
    result = dict(status='CIUA_A3_FORMAL_READ_ONLY_FREEZE_PASS', request_sha256=SHA, archive_sha256=receipt['sha256'], inventory=inventory, case_count=40, archived_members=46, head_calls=120, call_events=240, resource_records=81, new_head_calls=0, replay_max_component_mm=max(r['replay_max_component_mm'] for r in case_rows), metrics=aggregates, cases=case_rows, state_rng_evidence='Frozen implementation asserts equality per case. Raw fingerprints were not persisted.')
    with (ROOT/'A3_formal_freeze_receipt_v1.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','archive_sha256','replay_max_component_mm','metrics')}))


if __name__ == '__main__':
    main()
