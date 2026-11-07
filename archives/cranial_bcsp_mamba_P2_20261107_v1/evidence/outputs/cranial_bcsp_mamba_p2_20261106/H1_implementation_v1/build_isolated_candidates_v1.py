"""One local implementation materialization. No imports/execution of model or server calls."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P1 = ROOT / 'outputs/cranial_bcsp_mamba_p1_20261104'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)

def write(name, text):
    ast.parse(text)
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as f:
        f.write(text)

runtime_parent = P1 / 'minimal_implementation_v1/bcsp_p1_training_runtime_v1.py'
assert digest(runtime_parent) == '939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee'
s = runtime_parent.read_text(encoding='utf-8')
helper = '''
def h1_log_components(model, ret, target, total_loss):
    """Detached O(N) diagnostics; never adds loss or recomputes Chamfer/forward."""
    enabled = model.coarse_geometry_guard_enabled
    with torch.no_grad():
        if enabled:
            require(model.coarse_geometry_guard_mode == 'centroid_radius'
                    and model.coarse_geometry_guard_weight == .1
                    and model.coarse_geometry_guard_beta == .1
                    and model.coarse_geometry_guard_eps == 1e-6, 'unique H1 formula')
            fn = model.get_loss.__func__.__globals__['coarse_geometry_guard_components']
            c = fn(ret[0], target, smooth_l1_beta=.1, cvar_fraction=.1,
                   eps=1e-6, requested_mode='centroid_radius')
            raw = c['centroid_radius']
            center, radius = c['centroid'], c['radius']
        else:
            raw = center = radius = total_loss.new_zeros(())
        weighted = raw * .1 if enabled else raw
        values = {'H1_enabled': bool(enabled), 'H1_centroid': float(center),
                  'H1_radius': float(radius), 'H1_raw': float(raw),
                  'H1_weighted': float(weighted),
                  'loss_without_H1_derived': float(total_loss.detach() - weighted),
                  'H1_log_is_detached_recomputation': True}
        require(all(__import__('math').isfinite(v) for v in values.values()
                    if type(v) is float), 'finite H1 diagnostic')
        return values

'''
s = replace_once(s, 'def train_lifecycle(', helper + 'def train_lifecycle(')
s = replace_once(s, "                    loss = sparse + dense\n", "                    loss = sparse + dense\n                    h1_event = h1_log_components(model, ret, target, loss)\n")
s = replace_once(s, "                    metrics.write(json.dumps(event, allow_nan=False) + '\\n')", "                    event.update(h1_event)\n                    metrics.write(json.dumps(event, allow_nan=False) + '\\n')")
s = '# P2 H1 derivative: only detached H1 diagnostics added; loss/update lifecycle unchanged.\n' + s
write('bcsp_p2_h1_training_runtime_v1.py', s)
runtime_sha = digest(HERE / 'bcsp_p2_h1_training_runtime_v1.py')

entry_parent = P1 / 'training_entry_v1/bcsp_p1_training_entry_v1.py'
s = entry_parent.read_text(encoding='utf-8')
s = ''.join(line for line in s.splitlines(keepends=True)
            if not line.startswith(('PINNED_IMPL=', 'PINNED_EVIDENCE=', 'QUANT_REQUEST_SHA=')))
t = ast.parse(s)
fn = next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == 'authorize')
lines = s.splitlines(keepends=True)
s = ''.join(lines[:fn.lineno-1]) + '__P2_AUTHORIZE__\n\n' + ''.join(lines[fn.end_lineno:])
baseline_paths = {
    'C': (P1 / 'M0_training_entry_v2/transport_payload/M0_foldC_seed0_training_execution_request_v1.json', P1 / 'M0_training_entry_v2/post_training_and_pair_freeze_audit_v1/audit_report_v1.json'),
    'D': (P1 / 'M0_FoldD_request_v1/transport_payload/M0_foldD_seed0_training_execution_request_v1.json', P1 / 'M0_FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json'),
}
pins = {k: dict(request_sha256=digest(a), audit_sha256=digest(b)) for k, (a,b) in baseline_paths.items()}
for fold, (a,b) in baseline_paths.items():
    assert json.loads(b.read_bytes())['request_sha256'] == digest(a), fold

authorize = '''H1 = dict(enabled=True, mode='centroid_radius', weight=.1, smooth_l1_beta=.1,
          cvar_fraction=.1, eps=1e-6)
FROZEN_BASELINES = __BASELINES__
H1_RUNTIME_SHA = '__RUNTIME_SHA__'

def validate_static_h1(static, baseline, metadata):
    import copy
    stripped = copy.deepcopy(static)
    require(stripped['model'].pop('coarse_geometry_guard', None) == H1, 'unique H1 config')
    require(stripped == baseline, 'H1-only config delta')
    metadata.validate_static(baseline)
    require(static['counts'] == COUNTS and static['resources'] == RESOURCES, 'counts/resources')
    return static

def validate_model_h1(model):
    require(model.num_query == 256 and model.num_points == 8192 and model.factor == 32
            and model.decoder_type == 'fc' and model.denoise_weight == 0
            and model.fine_coverage_weight == 1 and model.fine_local_weight == 0, 'model contract')
    base = model.base_model
    require(base.center_num == [512,256] and base.encoder_type == 'graph'
            and base.query_selection == 'learned_only' and not base.use_denoise
            and not base.encoder_adapter.enabled and not model.scqr_contract.enabled, 'backbone contract')
    for name in ('local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled'):
        require(getattr(model,name) is False, 'optional path: '+name)
    require(model.coarse_geometry_guard_enabled is True
            and model.coarse_geometry_guard_mode == H1['mode']
            and model.coarse_geometry_guard_weight == H1['weight']
            and model.coarse_geometry_guard_beta == H1['smooth_l1_beta']
            and model.coarse_geometry_guard_cvar_fraction == H1['cvar_fraction']
            and model.coarse_geometry_guard_eps == H1['eps'], 'actual H1 config')

def authorize(qr, ar, rr):
    q = json_bound(qr)
    extra = {'baseline_request','baseline_audit','h1_formula','p3','h1_config'}
    base = json_bound(q['baseline_request'])
    require(set(q) == set(base) | extra, 'exact P2 request fields')
    require(q['schema'] == 'bcsp-p2-H1-training-request-v1'
            and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION'
            and q['stage'] == 'CRANIAL_BCSP_MAMBA_P2_H1'
            and q['variant'] == 'M0' and q['fold'] in ('C','D'), 'pending M-H1 request')
    pin = FROZEN_BASELINES[q['fold']]
    require(q['baseline_request']['sha256'] == pin['request_sha256']
            and q['baseline_audit']['sha256'] == pin['audit_sha256'], 'frozen baseline')
    audit = json_bound(q['baseline_audit'])
    require(audit['status'] == 'FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
            and audit['request_sha256'] == pin['request_sha256']
            and audit['checks_passed'] == len(audit['checks']) > 0
            and all(audit['checks'].values()), 'baseline formal audit')
    changed = {'schema','stage','run_id','static_config','implementation','output','launch_attempt',
               'launch_contract','provenance','not_authorized'}
    require(all(q[k] == v for k,v in base.items() if k not in changed), 'baseline scientific/environment pairing')
    require(base['variant'] == 'M0' and base['fold'] == q['fold']
            and q['n_input'] == q['n_output'] == 8192, 'M0 fold/8k pairing')
    a, r = json_bound(ar), json_bound(rr)
    require(set(a) == {'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
            and a['schema'] == 'bcsp-p2-H1-training-authorization-v1'
            and a['request_sha256'] == qr['sha256'] and a['explicit_user_authorization'] is True
            and bool(a['user_authorization_text'].strip()), 'separate user authorization')
    require(r == dict(schema='bcsp-p2-H1-training-runtime-v1',request_sha256=qr['sha256'],
                      authorization_sha256=ar['sha256']), 'one-way runtime')
    require(set(q['implementation']) == set(base['implementation']), 'implementation set')
    for k,v in base['implementation'].items():
        if k not in ('entry','runtime'): require(q['implementation'][k] == v, 'unchanged implementation '+k)
    require(q['implementation']['runtime']['sha256'] == H1_RUNTIME_SHA, 'H1 logging runtime')
    for v in q['implementation'].values(): exact(v)
    require(exact(q['implementation']['entry']) == Path(__file__).absolute(), 'entry origin')
    formula = json_bound(q['h1_formula'])
    require(q['h1_config'] == H1 and formula['parameters'] == H1
            and formula['cvar_branch_executed'] is False, 'frozen H1 formula')
    p3 = json_bound(q['p3'])
    require(p3['status'] == 'LOCAL_P2_H1_IMPLEMENTATION_P3_PASS'
            and p3['entry_sha256'] == q['implementation']['entry']['sha256']
            and p3['runtime_sha256'] == H1_RUNTIME_SHA, 'final P3 hashes')
    metadata = load_bound('bcsp_training_contract_v1', q['implementation']['contract'])
    static = validate_static_h1(json_bound(q['static_config']), json_bound(base['static_config']), metadata)
    selected, fold = metadata.verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']),
        q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],q['fold'],8192)
    plan = metadata.validate_order(json_bound(q['order_plan']), fold['train_case_ids'])
    return q, static, metadata, selected, fold, plan
'''.replace('__BASELINES__', repr(pins)).replace('__RUNTIME_SHA__', runtime_sha)
s = s.replace('__P2_AUTHORIZE__', authorize)
s = replace_once(s, '    helper.validate_model(model)', '    validate_model_h1(model)')
s = replace_once(s, "    require(q['variant'] in ('T0','M0'),'model dispatch variant')", "    require(q['variant']=='M0','M-H1 only')")
s = s.replace("PROJECT+'/logs/cranial_bcsp_mamba_p1'", "PROJECT+'/logs/cranial_bcsp_mamba_p2_h1'")
s = replace_once(s, "require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config')", "require({k:v for k,v in static['model'].items() if k != 'coarse_geometry_guard'}==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'H1-only model config delta')")
# The full P1 factory fingerprints remain identical: H1 introduces no parameters.
s = '# Isolated P2 derivative; unchanged P1 I/O policy, monitoring, initialization and dispatch lifecycle.\n' + s
write('bcsp_p2_h1_training_entry_v1.py', s)
print(json.dumps({'status':'CANDIDATES_CREATED_NOT_TESTED','baseline_pins':pins,'runtime_sha256':runtime_sha,
                  'entry_sha256':digest(HERE/'bcsp_p2_h1_training_entry_v1.py')}, indent=2))
