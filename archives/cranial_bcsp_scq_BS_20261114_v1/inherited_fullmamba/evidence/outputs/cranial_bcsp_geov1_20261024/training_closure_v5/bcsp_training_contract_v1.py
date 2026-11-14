"""BCSP training-only metadata contracts. No torch, payload or automatic execution."""
import hashlib
import json
from pathlib import Path, PurePosixPath

STAGE = 'BCSP_INPUT_DENSITY_V1'
QC_STATUS = 'PASS_GEOMETRIC_PAIRING_SOURCE_QC_WITH_DECLARED_SEMANTIC_LIMITS'
GPU_STATUS = 'FORMAL_POST_PREFLIGHT_FREEZE_AUDIT_PASS'
COUNTS = {'cases': 315, 'sources': 63, 'batch': 8, 'epochs': 100,
          'batches_per_epoch': 39, 'updates': 3900, 'exposures': 31200}
LIMITS = ('Separate inner/outer plate coverage not certified',
          'Representation QC is not prediction or clinical accuracy',
          'Artificial GPU zero-update success is not complete training memory proof')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def no_links(path):
    p = Path(path).absolute()
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'linked path: ' + str(p))
    return p


def exact(record):
    require(isinstance(record, dict) and set(record) == {'path', 'bytes', 'sha256'}, 'exact binding fields')
    p = no_links(record['path'])
    require(p.is_file() and p.stat().st_size == record['bytes'] and sha(p) == record['sha256'],
            'bound file drift: ' + str(p))
    return p


def json_bound(record):
    return json.loads(exact(record).read_text(encoding='utf-8'))


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode('utf-8')).hexdigest()


def emit(path, value):
    with no_links(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def bind_metadata(verification, manifests, fold_binding, fold, n_input):
    """Qualified reader/writer mapping; does not reopen or certify payload bytes."""
    require(fold in ('C', 'D') and n_input in (8192, 16384), 'fold/arm')
    qc = json_bound(verification)
    require(qc.get('status') == QC_STATUS and qc.get('verified_sources') == 84
            and qc.get('verified_cases') == 420 and qc.get('verified_point_files') == 840,
            'qualified QC identity/counts')
    require(qc.get('interpretation', {}).get('anatomical_semantics', '').startswith('UNRESOLVED'),
            'QC anatomical limitation missing')
    require(set(manifests) == {'8192', '16384'}, 'both manifests required')
    records = {}
    for arm in ('8192', '16384'):
        path = exact(manifests[arm])
        require(qc['important_file_hashes']['manifest_' + arm + '.jsonl'] == manifests[arm]['sha256'],
                'manifest not bound by original QC')
        values = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
        records[arm] = {r['case_id']: r for r in values}
        require(len(values) == len(records[arm]) == 420, 'manifest duplicate/count')
    require(set(records['8192']) == set(records['16384']), 'paired case identity')
    for cid, a in records['8192'].items():
        b = records['16384'][cid]
        require(all(a[k] == b[k] for k in ('source_id', 'target_array_sha256', 'normalization', 'raw')),
                'paired provenance/target/frame mismatch')
        require(a.get('schema') == b.get('schema') == 'BCSP-normalized-v1'
                and a.get('normalization_source') == b.get('normalization_source') == 'defective_bbox',
                'geometry schema/frame')
        require((a['n_input'], b['n_input'], a['n_target'], b['n_target']) == (8192, 16384, 8192, 8192),
                'point counts')
    folds = json_bound(fold_binding)
    spec = folds['folds'][fold]
    ids, sources, dev = spec['train_case_ids'], spec['train_sources'], spec['dev_sources']
    require(len(ids) == len(set(ids)) == 315 and len(sources) == len(set(sources)) == 63
            and len(dev) == 21 and not set(sources) & set(dev), 'source fold boundary')
    require(folds.get('confirmation_count_excluded') == 20, 'confirmation exclusion')
    require(hashlib.sha256(('\n'.join(ids) + '\n').encode()).hexdigest() == spec['train_allowlist_sha256'],
            'case allowlist hash')
    selected = [records[str(n_input)][cid] for cid in ids]
    counts = {s: 0 for s in sources}
    for r in selected:
        require(r['source_id'] in counts, 'source not train')
        counts[r['source_id']] += 1
        rel = PurePosixPath(r['point_path'])
        require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in r['point_path']
                and rel.suffix == '.npz', 'relative point path')
    require(set(counts.values()) == {5}, 'five defects per source')
    receipt = {'schema': 'bcsp-training-qualified-QC-v1', 'status': 'QUALIFIED_FOR_FIXED_TRAINING_GEOMETRY',
               'verification': verification, 'manifests': manifests, 'fold_binding': fold_binding,
               'fold': fold, 'n_input': n_input, 'manifest_sha256': manifests[str(n_input)]['sha256'],
               'train_allowlist_sha256': spec['train_allowlist_sha256'],
               'limitations': list(LIMITS), 'payload_reverified_by_this_mapping': False}
    return receipt, selected, spec


def verify_qualified_receipt(receipt, verification, manifests, fold_binding, fold, n_input):
    expected, selected, spec = bind_metadata(verification, manifests, fold_binding, fold, n_input)
    require(receipt == expected, 'qualified receipt drift or dropped limitations')
    return selected, spec


def validate_static(config):
    require(set(config) == {'schema', 'stage', 'counts', 'model', 'training', 'resources'}, 'static fields')
    require(config['schema'] == 'bcsp-training-static-v1' and config['stage'] == STAGE
            and config['counts'] == COUNTS and all(type(v) is int for v in config['counts'].values()),
            'stage/count contract')
    t = config['training']
    require(t == {'seed': 0, 'precision': 'FP32', 'optimizer': 'AdamW', 'lr': .0001,
                  'weight_decay': .0005, 'clip': 10, 'step_per_update': 1, 'drop_last': True,
                  'checkpoint': 'scratch_final_only', 'BNCal': False, 'evaluation': False,
                  'resume': False}, 'training scientific contract')
    m = config['model']
    require(m.get('num_query') == 256 and m.get('num_points') == 8192 and m.get('center_num') == [512, 256]
            and m.get('encoder_type') == 'graph' and m.get('decoder_type') == 'fc'
            and m.get('query_selection') == 'learned_only' and m.get('denoise_weight') == 0,
            'B0 model contract')
    r = config['resources']
    require(set(r) == {'wall_seconds', 'RSS_bytes', 'device_MiB', 'torch_peak_bytes', 'output_bytes',
                       'minimum_free_disk_bytes'}, 'training resource fields')
    require(all(type(v) is int and v > 0 for v in r.values()), 'explicit positive integer budgets required')
    require(r['RSS_bytes'] == 8 * 1024**3 and r['device_MiB'] == 22528
            and r['torch_peak_bytes'] == 20 * 1024**3
            and r['minimum_free_disk_bytes'] >= 2 * 1024**3, 'unchanged memory ceilings/minimum disk')
    require(r['output_bytes'] >= 1048576, 'output budget must be explicit and usable')
    return config


def authorize(request_record, authorization_record, runtime_record):
    """Static config -> request -> authorization hash -> runtime; no reverse edges."""
    q = json_bound(request_record)
    require(set(q) == {'schema', 'stage', 'status', 'run_id', 'fold', 'n_input', 'static_config',
                      'QC', 'order_plan', 'GPU_audit', 'preflight_request_sha256', 'preflight_scope',
                      'identity', 'data_root', 'model_root', 'implementation', 'output', 'launch_attempt'},
            'request fields; no reverse authorization/runtime/config bindings')
    require(q.get('schema') == 'bcsp-training-request-v1' and q.get('stage') == STAGE
            and q.get('status') == 'AWAITING_EXPLICIT_USER_AUTHORIZATION', 'pending training request required')
    config = validate_static(json_bound(q['static_config']))
    auth = json_bound(authorization_record)
    require(set(auth) == {'schema', 'request_sha256', 'explicit_user_authorization', 'user_authorization_text'}
            and auth['schema'] == 'bcsp-training-authorization-v1'
            and auth['request_sha256'] == request_record['sha256']
            and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),
            'separate authorization; reverse binding forbidden')
    runtime = json_bound(runtime_record)
    require(runtime == {'schema': 'bcsp-training-runtime-v1', 'request_sha256': request_record['sha256'],
                        'authorization_sha256': authorization_record['sha256']}, 'one-way runtime binding')
    gpu = json_bound(q['GPU_audit'])
    require(gpu.get('status') == GPU_STATUS and gpu.get('request_sha256') == q['preflight_request_sha256'],
            'actual frozen GPU evidence required, not boolean readiness')
    require(q.get('fold') in ('C', 'D') and q.get('n_input') in (8192, 16384), 'fold/input')
    return q, config


def validate_order(plan, ids):
    require(set(plan) == {'schema', 'case_ids', 'epochs'} and plan['schema'] == 'bcsp-shared-order-v1'
            and plan['case_ids'] == ids and len(ids) == len(set(ids)) == 315
            and len(plan['epochs']) == 100, 'shared order schema')
    for epoch, row in enumerate(plan['epochs']):
        require(set(row) == {'epoch', 'batches', 'dropped'} and row['epoch'] == epoch
                and len(row['batches']) == 39 and all(len(b) == 8 for b in row['batches'])
                and len(row['dropped']) == 3, 'epoch order counts')
        flat = [i for batch in row['batches'] for i in batch] + row['dropped']
        require(len(flat) == len(set(flat)) == 315 and set(flat) == set(ids), 'order case set/duplicates')
    return plan
