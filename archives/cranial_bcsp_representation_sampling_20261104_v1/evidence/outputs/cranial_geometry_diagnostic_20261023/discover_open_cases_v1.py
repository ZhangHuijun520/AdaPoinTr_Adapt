import hashlib
import importlib.util
import json
import os
import socket
from pathlib import Path

assert socket.gethostname() == 'shu-common-25721452-notebook-n9i64i-0'
assert os.getuid() == 1000
root = Path('/home/jovyan/datasets')
selected = []
for dataset in ['SkullFix', 'SkullBreak']:
    d = root / (dataset + 'PC')
    rows = [json.loads(x) for x in (d / 'manifest.jsonl').read_text().splitlines() if x.strip()]
    if dataset == 'SkullFix':
        allowed = set(json.loads((d / 'splits.json').read_text())['train'])
        candidates = [r for r in rows if r['case_id'] in allowed and r['split'] == 'train']
    else:
        allowed = set(json.loads((d / 'group_splits.json').read_text())['gate']['train'])
        candidates = [r for r in rows if r['skull_id'] in allowed and r['official_split'] == 'train' and r['defect_type'] == 'bilateral']
    for r in sorted(candidates, key=lambda x: x['case_id'])[:3]:
        selected.append({'dataset': dataset, 'root': str(d), 'record': r})
d = root / 'MUG500plusD6Development400_v1'
rows = [json.loads(x) for x in (d / 'manifest.jsonl').read_text().splitlines() if x.strip()]
candidates = [r for r in rows if r['d6_partition'] == 'development' and r['defect_type'] == 'ellipsoid_medium']
for r in sorted(candidates, key=lambda x: x['case_id'])[:3]:
    selected.append({'dataset': 'MUG500plus', 'root': str(d), 'record': r})
assert len(selected) == 9
for x in selected:
    r = x['record']
    p = Path(x['root']) / r['point_path']
    assert p.is_file()
    x['point_size'] = p.stat().st_size
    if x['dataset'] == 'MUG500plus':
        s = (Path(x['root']) / r['source_asset_path']).resolve(strict=True)
        assert s.is_relative_to(root / 'MUG500plusD6Development100_v1')
        x['resolved_source'] = str(s)
        x['source_size'] = s.stat().st_size
print(json.dumps({'selected': selected, 'modules': {m: bool(importlib.util.find_spec(m)) for m in ['numpy','scipy','matplotlib','trimesh','skimage','nrrd']}, 'hostname': socket.gethostname()}, ensure_ascii=False))
