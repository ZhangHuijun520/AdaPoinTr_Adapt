"""Exactly 12 artificial CPU contracts; no CUDA, payload, model or server execution."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '2'
ROOT = Path(__file__).absolute().parent
BASE = ROOT.parent
ARTIFACT = ROOT / 'artificial_cpu_batch_v1'
FIX = ARTIFACT / 'fixtures'
OLD = BASE / 'training_closure_v5'
FREEZE = BASE / 'first_run_freeze_foldC_8192_v1'
PREFLIGHT = BASE / 'gpu_preflight_plotting_lazy_v3'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def binding(p):
    p = Path(p).absolute()
    return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest(p)}


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def write(name, value):
    p = FIX / name
    with p.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
    return binding(p)


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def rejects(call, fragment=None, exceptions=(ValueError, RuntimeError, FileNotFoundError)):
    try:
        call()
    except exceptions as exc:
        if fragment:
            assert fragment in str(exc), (fragment, str(exc))
        return
    raise AssertionError('expected rejection')


def trees(p):
    return {x.name: ast.dump(x, include_attributes=False) for x in
            ast.parse(Path(p).read_text(encoding='utf-8')).body
            if isinstance(x, (ast.FunctionDef, ast.ClassDef))}


def fresh_q():
    return {'schema': 'bcsp-training-request-v2', 'stage': C.STAGE,
            'status': 'AWAITING_EXPLICIT_USER_AUTHORIZATION', 'run_id': 'ARTIFICIAL_ONLY_NOT_EXECUTABLE',
            'fold': 'C', 'n_input': 8192, 'static_config': binding(FREEZE / 'static_training_config_v1.json'),
            'QC': {}, 'order_plan': binding(FREEZE / 'shared_order_foldC_seed0_v1.json'),
            'GPU_audit': GPU, 'preflight_request_sha256': read(GPU['path'])['request_sha256'],
            'preflight_scope': SCOPE, 'identity': RECEIPT['new_identity'],
            'data_root': 'ARTIFICIAL_NO_PAYLOAD', 'model_root': 'ARTIFICIAL_NO_MODEL',
            'implementation': {'runtime': {'sha256': C.IMMUTABLE['training_runtime']}},
            'output': 'ARTIFICIAL_NOT_LAUNCHABLE', 'launch_attempt': 'ARTIFICIAL_NOT_CLAIMED',
            'resource_rebind': REBIND}


SERIAL = 0
def chain(q=None, change_auth=None, change_runtime=None):
    global SERIAL
    SERIAL += 1
    q = fresh_q() if q is None else q
    qr = write('request_artificial_' + str(SERIAL) + '.json', q)
    a = {'schema': 'bcsp-training-authorization-v1', 'request_sha256': qr['sha256'],
         'explicit_user_authorization': True, 'user_authorization_text': 'SYNTHETIC CPU fixture; no real execution authority'}
    if change_auth:
        change_auth(a)
    ar = write('authorization_artificial_' + str(SERIAL) + '.json', a)
    r = {'schema': 'bcsp-training-runtime-v1', 'request_sha256': qr['sha256'],
         'authorization_sha256': ar['sha256']}
    if change_runtime:
        change_runtime(r)
    rr = write('runtime_artificial_' + str(SERIAL) + '.json', r)
    return qr, ar, rr


def R01():
    pins = {
        OLD / 'bcsp_training_contract_v1.py': 'e57d0b6b23fe6a741d82e6de65e4ab7f911d8bb06c2d767ec19465ee92324b91',
        OLD / 'bcsp_training_entry_v1.py': '978326c599100dc5e131239254db44dd5a1a40625fa2eccbb21c583290aa60d4',
        OLD / 'bcsp_training_runtime_v5.py': C.IMMUTABLE['training_runtime'],
        FREEZE / 'static_training_config_v1.json': C.IMMUTABLE['static_config'],
        FREEZE / 'shared_order_foldC_seed0_v1.json': C.IMMUTABLE['order_plan'],
        FREEZE / 'transport_scope_v1.json': C.IMMUTABLE['transport_scope'],
        PREFLIGHT / 'bcsp_artificial_gpu_preflight_v3.py': E.PREFLIGHT_SHA,
    }
    for path, sha in pins.items():
        assert digest(path) == sha, str(path)
    for old, new, changed in (
        (OLD / 'bcsp_training_contract_v1.py', ROOT / 'bcsp_training_contract_v2.py', {'authorize'}),
        (OLD / 'bcsp_training_entry_v1.py', ROOT / 'bcsp_training_entry_v2.py', {'main', 'install_contract'}),
    ):
        a, b = trees(old), trees(new)
        assert all(b[k] == v for k, v in a.items() if k not in changed)


def R02():
    assert C.validate_rebind(REBIND, SCOPE, GPU) == RECEIPT
    assert digest(ROOT / RECEIPT['new_readonly_report']['path']) == RECEIPT['new_readonly_report']['sha256']
    for record, field in ((SCOPE, 'old_scope_sha256'), (GPU, 'historical_GPU_audit_sha256')):
        assert record['sha256'] == RECEIPT[field]
    altered = dict(SCOPE, sha256='0' * 64)
    rejects(lambda: C.validate_rebind(REBIND, altered, GPU), 'historical evidence')


def R03():
    assert {k for k in RECEIPT['old_identity'] if RECEIPT['old_identity'][k] != RECEIPT['new_identity'][k]} == {
        'hostname', 'gpu_uuid', 'driver_version'}
    for k, value in [('uid', 0), ('nvidia_smi_memory_total_MiB', 30000), ('python_version', '3.9'),
                     ('gpu_name', 'different'), ('project', '/elsewhere'), ('extra', True)]:
        r = copy.deepcopy(RECEIPT)
        r['new_identity'][k] = value
        rejects(lambda: C.validate_rebind_value(r, SCOPE_VALUE, REPORT), 'identity changes')
    r = copy.deepcopy(RECEIPT)
    r['identity_differences'].pop()
    rejects(lambda: C.validate_rebind_value(r, SCOPE_VALUE, REPORT), 'delta list')


def R04():
    observed = dict(C.IDENTITY_UPDATES)
    C.validate_live_identity(RECEIPT['new_identity'], observed)
    for key in observed:
        bad = dict(observed, **{key: 'WRONG'})
        rejects(lambda: C.validate_live_identity(RECEIPT['new_identity'], bad), 'live rebound')
    rejects(lambda: C.validate_live_identity(RECEIPT['new_identity'], dict(observed, extra=1)))


def R05():
    C.authorize(*chain())
    for value in (None, False, True, dict(REBIND, sha256='0' * 64)):
        q = fresh_q()
        q['resource_rebind'] = value
        rejects(lambda: C.authorize(*chain(q)))
    q = fresh_q()
    del q['resource_rebind']
    rejects(lambda: C.authorize(*chain(q)), 'request fields')
    bad = write('drifted_receipt.json', dict(RECEIPT, status='DRIFT'))
    rejects(lambda: C.validate_rebind(bad, SCOPE, GPU), 'receipt pin')


def R06():
    expected = C.expected_environment(SCOPE_VALUE, RECEIPT['new_identity'], '/owned')
    assert expected['CUDA_VISIBLE_DEVICES'] == C.IDENTITY_UPDATES['gpu_uuid']
    C.validate_environment(SCOPE_VALUE, RECEIPT['new_identity'], '/owned', expected)
    for wrong in (SCOPE_VALUE['identity']['gpu_uuid'], '0', 'GPU-arbitrary', ''):
        rejects(lambda: C.validate_environment(SCOPE_VALUE, RECEIPT['new_identity'], '/owned',
                                               dict(expected, CUDA_VISIBLE_DEVICES=wrong)), 'CUDA_VISIBLE_DEVICES')
    assert read(SCOPE['path'])['environment']['CUDA_VISIBLE_DEVICES'] == RECEIPT['old_identity']['gpu_uuid']


def R07():
    expected = C.expected_environment(SCOPE_VALUE, RECEIPT['new_identity'], '/owned')
    for key in expected:
        if key != 'CUDA_VISIBLE_DEVICES':
            altered = dict(expected)
            altered[key] = 'WRONG'
            rejects(lambda: C.validate_environment(SCOPE_VALUE, RECEIPT['new_identity'], '/owned', altered), key)
    # Entire payload/secret/link policy and resource monitor are byte-for-byte AST identical.
    old, new = trees(OLD / 'bcsp_training_entry_v1.py'), trees(ROOT / 'bcsp_training_entry_v2.py')
    for name in ('make_training_policy', 'payload_paths', 'TrainingBudget', 'verify_timeout'):
        assert old[name] == new[name]
    # Exercise the unchanged policy with artificial paths and a CPU-only base.
    class BasePolicy:
        def __init__(self, roots, output):
            self.output = Path(output).absolute()
        def check(self, filename, write=False):
            return 'base guard retained'
    class Helper:
        FilePolicy = BasePolicy
        PAYLOAD = {'.pth', '.stl', '.nrrd', '.npz'}
    policy = E.make_training_policy(Helper, [], FIX, {FIX / 'allowed.npz': 'fake'})
    policy.check(FIX / 'allowed.npz')
    rejects(lambda: policy.check(FIX / 'allowed.npz', True), 'NPZ')
    for p in (FIX / 'other.npz', FIX / 'forbidden.pth', FIX / '.ssh' / 'key', FIX / '.env'):
        rejects(lambda: policy.check(p))
    helper_ast = ast.parse((PREFLIGHT / 'bcsp_artificial_gpu_preflight_v3.py').read_text(encoding='utf-8'))
    assert any(isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value == 'socket.'
               for n in ast.walk(helper_ast)), 'inherited network audit guard'


def R08():
    cfg = read(FREEZE / 'static_training_config_v1.json')
    C.validate_static(cfg)
    for section, key, val in [('counts', 'updates', 3899), ('counts', 'epochs', 101),
                              ('training', 'BNCal', True), ('training', 'resume', True),
                              ('resources', 'device_MiB', 24564), ('model', 'num_points', 16384)]:
        bad = copy.deepcopy(cfg)
        bad[section][key] = val
        rejects(lambda: C.validate_static(bad))
    for field, value in [('fold', 'D'), ('n_input', 16384)]:
        q = fresh_q()
        q[field] = value
        rejects(lambda: C.authorize(*chain(q)), 'first rebound')
    q = fresh_q()
    q['static_config'] = write('modified_scientific_config.json',
                                dict(cfg, resources=dict(cfg['resources'], wall_seconds=100)))
    rejects(lambda: C.authorize(*chain(q)), 'unchanged scientific')
    rejects(lambda: C.bind_metadata({}, {}, {}, 'invalid', 8192), 'fold/arm')
    rejects(lambda: C.validate_order({'schema': 'WRONG'}, []), 'shared order')


def R09():
    for field, value in [('new_gpu_execution_validated', True), ('historical_GPU_evidence_only', False),
                         ('identity_binding_verified', 1), ('limitations', [])]:
        r = copy.deepcopy(RECEIPT)
        r[field] = value
        rejects(lambda: C.validate_rebind_value(r, SCOPE_VALUE, REPORT), 'historical evidence')
    r = copy.deepcopy(RECEIPT)
    r['compatibility_certified'] = True
    rejects(lambda: C.validate_rebind_value(r, SCOPE_VALUE, REPORT), 'receipt fields')


def R10():
    C.authorize(*chain())
    q = fresh_q()
    q['authorization_sha256'] = '0' * 64
    rejects(lambda: C.authorize(*chain(q)), 'request fields')
    rejects(lambda: C.authorize(*chain(change_auth=lambda a: a.update(runtime_sha256='0' * 64))),
            'reverse binding')
    rejects(lambda: C.authorize(*chain(change_runtime=lambda r: r.update(authorization_sha256='0' * 64))),
            'one-way')
    r = copy.deepcopy(RECEIPT)
    r['future_implementation_sha256'] = '0' * 64
    rejects(lambda: C.validate_rebind_value(r, SCOPE_VALUE, REPORT), 'reverse hash')


def R11():
    assert Path(sys.modules['bcsp_training_contract_v1'].__file__).absolute() == ROOT / 'bcsp_training_contract_v2.py'
    assert E.CONTRACT_SHA == digest(ROOT / 'bcsp_training_contract_v2.py')
    sandbox = FIX / 'bootstrap'
    sandbox.mkdir()
    entry = sandbox / 'bcsp_training_entry_v2.py'
    entry.write_bytes((ROOT / entry.name).read_bytes())
    # A valid old sibling is deliberately present; it must never be a fallback.
    (sandbox / 'bcsp_training_contract_v1.py').write_bytes((OLD / 'bcsp_training_contract_v1.py').read_bytes())
    rejects(lambda: load('missing_v2_sibling', entry), exceptions=(FileNotFoundError,))
    (sandbox / 'bcsp_training_contract_v2.py').write_text('# drift\n', encoding='utf-8')
    rejects(lambda: load('drifted_v2_sibling', entry), 'bootstrap identity')


def R12():
    qr, ar, rr = chain(change_auth=lambda a: a.update(explicit_user_authorization=False))
    args = [str(ROOT / 'bcsp_training_entry_v2.py')]
    for name, r in [('request', qr), ('authorization', ar), ('runtime', rr)]:
        args.extend(['--' + name, r['path'], '--' + name + '-sha256', r['sha256']])
    prior = sys.argv
    sys.argv = args
    E.payload_paths = lambda *a: (_ for _ in ()).throw(AssertionError('payload reached'))
    E.load_bound = lambda *a: (_ for _ in ()).throw(AssertionError('model/import reached'))
    try:
        rejects(E.main, 'separate authorization')
    finally:
        sys.argv = prior
    assert not any(name == 'torch' or name.startswith('torch.') for name in sys.modules)
    archive = FREEZE / 'transport_v1' / 'bcsp_foldc_8192_train_inputs_v1.tar.gz'
    manifest = archive.with_name('bcsp_foldc_8192_train_inputs_v1.contents.sha256')
    assert archive.stat().st_size == 49773476 and digest(archive) == C.IMMUTABLE['original_archive']
    assert digest(manifest) == C.IMMUTABLE['original_manifest']
    assert len(manifest.read_text(encoding='utf-8').splitlines()) == 327


def run():
    # Exclusive directory is the single-batch claim. Existing attempt is never reused.
    ARTIFACT.mkdir(exist_ok=False)
    FIX.mkdir()
    global E, C, RECEIPT, SCOPE, GPU, REBIND, SCOPE_VALUE, REPORT
    E = load('bcsp_rebind_entry_cpu_only', ROOT / 'bcsp_training_entry_v2.py')
    C = sys.modules['bcsp_training_contract_v1']
    REBIND = binding(ROOT / 'resource_rebind_receipt_v1.json')
    RECEIPT = read(REBIND['path'])
    SCOPE = binding(PREFLIGHT / 'artificial_gpu_zero_update_frozen_scope_v3.json')
    GPU = binding(PREFLIGHT / 'authorized_execution_v3/post_preflight_freeze_audit_report_v1.json')
    SCOPE_VALUE, REPORT = read(SCOPE['path']), read(ROOT / RECEIPT['new_readonly_report']['path'])
    start, results = time.monotonic(), []
    try:
        for i in range(1, 13):
            name = 'R' + str(i).zfill(2)
            globals()[name]()
            results.append({'id': name, 'status': 'PASS'})
            print(name + ' PASS', flush=True)
    except BaseException as exc:
        results.append({'id': name, 'status': 'FAIL', 'error': repr(exc)})
        raise
    finally:
        result = {'schema': 'bcsp-rebind-artificial-cpu-results-v1',
                  'status': 'PASS_12_ARTIFICIAL_CPU_ONLY' if len(results) == 12 and all(
                      x['status'] == 'PASS' for x in results) else 'FAIL_STOP_NO_RETRY',
                  'tests': results, 'elapsed_seconds': time.monotonic() - start,
                  'new_gpu_execution_validated': False, 'real_payload_reads': 0, 'server_operations': 0,
                  'model_forwards': 0, 'training_steps': 0}
        with (ARTIFACT / 'results_v1.json').open('x', encoding='utf-8', newline='\n') as f:
            json.dump(result, f, indent=2)
            f.write('\n')


if __name__ == '__main__':
    run()
