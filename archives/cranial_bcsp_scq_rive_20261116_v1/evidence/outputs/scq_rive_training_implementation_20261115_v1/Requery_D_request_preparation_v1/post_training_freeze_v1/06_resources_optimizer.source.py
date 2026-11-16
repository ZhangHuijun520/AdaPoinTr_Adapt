import pathlib, json, math, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = pathlib.Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1')
identity = json.loads((p / 'run_identity.json').read_bytes())
limits = identity['effective_resources']
rows = [json.loads(s) for s in (p / 'resources.jsonl').read_text().splitlines()]
assert len(rows) == 3902
peaks = {k: 0 for k in ('RSS', 'peak_allocated', 'peak_reserved', 'device_MiB', 'output_bytes', 'elapsed_seconds')}
previous = 0
for (i, r) in enumerate(rows):
    assert r['limits'] == limits and r['PID_policy'] == 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
    assert (r['phase'], r['committed_step']) == (('after_step', i + 1) if i < 3900 else ('before_final' if i == 3900 else 'after_final', 3900))
    checks = dict(allocated_within_limit=r['peak_allocated'] <= limits['torch_peak_bytes'], reserved_within_limit=r['peak_reserved'] <= limits['torch_peak_bytes'], device_within_limit=r['device_MiB'] <= limits['device_MiB'])
    assert checks == r['checks'] and all(checks.values()) and r['resource_guard_passed'] and (not r['failed_checks'])
    assert r['RSS'] <= limits['RSS_bytes'] and r['output_bytes'] <= limits['output_bytes'] and (previous <= r['elapsed_seconds'] <= 3600)
    previous = r['elapsed_seconds']
    for k in peaks:
        peaks[k] = max(peaks[k], r[k])
groups = json.loads((p / 'optimizer_parameter_groups.json').read_bytes())
assert len(groups) == len({r['name'] for r in groups}) == 419
for r in groups:
    assert r['weight_decay'] == (0 if r['reason'] in ('explicit_no_weight_decay', 'one_dimensional_or_bias') else 0.0005)
new = {r['name']: r['weight_decay'] for r in groups if r['name'].startswith(('base_model.scq.', 'base_model.rf.'))}
assert len(new) == 8
assert all((w == (0.0005 if n.endswith('weight') else 0) for (n, w) in new.items()))
assert all((r['weight_decay'] == 0 for r in groups if r['name'].endswith(('A_log', '.D'))))
d = json.loads((p / 'optimizer_actual_defaults.json').read_bytes())
assert d['lr'] == 0.0001 and d['betas'] == [0.9, 0.999] and (d['eps'] == 1e-08) and (not d['amsgrad']) and (d['foreach'] is None) and (d['fused'] is None)
print(json.dumps(dict(status='RESOURCES_AND_OPTIMIZER_PASS', resource_records=3902, parameters=419, new_groups=new, peaks=peaks, default_weight_decay=d['weight_decay'], actual_group_weight_decay=[0, 0.0005], sampled_RSS_not_hard_isolation=True)))
