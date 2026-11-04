"""One fail-fast artificial CPU batch. No real NPZ, checkpoint, model or server."""
import ast
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicitly hidden CUDA required'
import numpy as np
import torch
from torch.utils.data import DataLoader

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT = HERE / 'cpu_attempt_v1'
FIX = OUT / 'fixtures'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


entry = load('cpu_training_entry', HERE / 'bcsp_training_entry_v1.py')
c = sys.modules['bcsp_training_contract_v1']
helper = load('cpu_frozen_preflight_helper', BASE / 'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
tools = types.ModuleType('tools')
tools.__path__ = []
sys.modules['tools'] = tools
adapter = load('tools.bcsp_adapter', BASE / 'implementation_candidate_v4/overlay/tools/bcsp_adapter.py')
r = load('cpu_training_runtime', HERE / 'bcsp_training_runtime_v5.py')


def binding(path):
    return {'path': str(path.absolute()), 'bytes': path.stat().st_size, 'sha256': c.sha(path)}


def write(name, value):
    path = FIX / name
    path.parent.mkdir(parents=True, exist_ok=True)
    c.emit(path, value)
    return binding(path)


def make_fixture():
    sources = ['ARTIFICIAL:%03d' % i for i in range(84)]
    records = {}
    manifests = {}
    for n in (8192, 16384):
        values = [{'case_id': 'ART_%03d_%d' % (i, j), 'source_id': source,
                   'point_path': 'points/ART_%03d_%d_%d.npz' % (i, j, n), 'sha256': '0' * 64,
                   'schema': 'BCSP-normalized-v1', 'normalization_source': 'defective_bbox',
                   'n_input': n, 'n_target': 8192, 'target_array_sha256': '1' * 64,
                   'normalization': {'center': [0, 0, 0], 'scale': 1}, 'raw': {'fixture_only': True}}
                  for i, source in enumerate(sources) for j in range(5)]
        p = FIX / ('artificial_manifest_%d.jsonl' % n)
        with p.open('x', encoding='utf-8') as stream:
            for value in values:
                stream.write(json.dumps(value) + '\n')
        records[n], manifests[str(n)] = values, binding(p)
    verification = write('artificial_QC.json', {
        'status': c.QC_STATUS, 'verified_sources': 84, 'verified_cases': 420, 'verified_point_files': 840,
        'interpretation': {'anatomical_semantics': 'UNRESOLVED_ARTIFICIAL_FIXTURE'},
        'important_file_hashes': {'manifest_' + n + '.jsonl': m['sha256'] for n, m in manifests.items()}})
    import hashlib
    ids = [v['case_id'] for v in records[8192][:315]]
    fold = {'train_case_ids': ids, 'train_sources': sources[:63], 'dev_sources': sources[63:],
            'train_allowlist_sha256': hashlib.sha256(('\n'.join(ids) + '\n').encode()).hexdigest()}
    fb = write('artificial_folds.json', {'confirmation_count_excluded': 20, 'folds': {'C': fold, 'D': fold}})
    qualified, selected, spec = c.bind_metadata(verification, manifests, fb, 'C', 8192)
    plan = r.make_order(ids)
    config = {'schema': 'bcsp-training-static-v1', 'stage': c.STAGE, 'counts': dict(c.COUNTS),
              'model': {'num_query': 256, 'num_points': 8192, 'center_num': [512, 256],
                        'encoder_type': 'graph', 'decoder_type': 'fc', 'query_selection': 'learned_only',
                        'denoise_weight': 0},
              'training': {'seed': 0, 'precision': 'FP32', 'optimizer': 'AdamW', 'lr': .0001,
                           'weight_decay': .0005, 'clip': 10, 'step_per_update': 1, 'drop_last': True,
                           'checkpoint': 'scratch_final_only', 'BNCal': False, 'evaluation': False, 'resume': False},
              'resources': {'wall_seconds': 3600, 'RSS_bytes': 8 * 1024**3, 'device_MiB': 22528,
                            'torch_peak_bytes': 20 * 1024**3, 'output_bytes': 32 * 1024**2,
                            'minimum_free_disk_bytes': 2 * 1024**3}}
    static = write('artificial_static.json', config)
    gpu = write('artificial_GPU_audit.json', {'status': c.GPU_STATUS, 'request_sha256': 'ARTIFICIAL'})
    request = {'schema': 'bcsp-training-request-v1', 'stage': c.STAGE,
               'status': 'AWAITING_EXPLICIT_USER_AUTHORIZATION', 'run_id': 'ARTIFICIAL_CPU_ONLY',
               'fold': 'C', 'n_input': 8192, 'static_config': static,
               'QC': {'verification': verification, 'manifests': manifests, 'fold_binding': fb,
                      'qualified_receipt': write('artificial_qualified.json', qualified)},
               'order_plan': write('artificial_order.json', plan), 'GPU_audit': gpu,
               'preflight_request_sha256': 'ARTIFICIAL', 'preflight_scope': {}, 'identity': {},
               'data_root': str(FIX), 'model_root': str(FIX), 'implementation': {},
               'output': str(FIX / 'NOT_A_REAL_TRAINING_RUN'), 'launch_attempt': str(FIX / 'UNUSED')}
    req = write('artificial_request.json', request)
    auth = write('artificial_authorization.json', {'schema': 'bcsp-training-authorization-v1',
                 'request_sha256': req['sha256'], 'explicit_user_authorization': True,
                 'user_authorization_text': 'ARTIFICIAL CPU FIXTURE, NOT SERVER AUTHORIZATION'})
    runtime = write('artificial_runtime.json', {'schema': 'bcsp-training-runtime-v1',
                    'request_sha256': req['sha256'], 'authorization_sha256': auth['sha256']})
    return types.SimpleNamespace(verification=verification, manifests=manifests, folds=fb,
                                 qualified=qualified, selected=selected, fold=spec, plan=plan,
                                 config=config, request=request, req=req, auth=auth, runtime=runtime)


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(3, 3)
        self.bn = torch.nn.BatchNorm1d(3)

    def forward(self, x):
        return self.bn(self.linear(x.mean(1)))

    def get_loss(self, ret, target, epoch, partial):
        return ret.new_zeros(()), (ret - target.mean(1)).square().mean()


class TensorBatches:
    def __init__(self, plan, epoch, records, drift=False):
        self.batches = plan['epochs'][epoch]['batches']
        self.source = {x['case_id']: x['source_id'] for x in records}
        self.x = torch.arange(48, dtype=torch.float32).reshape(8, 2, 3) / 50
        self.y = torch.zeros_like(self.x)
        self.drift = drift

    def __len__(self):
        return 39

    def __iter__(self):
        for ids in self.batches:
            actual = list(reversed(ids)) if self.drift else ids
            yield self.x, self.y, actual, [self.source[i] for i in actual]


class CPUResourceFixture:
    def __init__(self):
        self.before, self.after, self.final = [], [], []

    def before_step(self, step):
        self.before.append(step)

    def after_step(self, step):
        self.after.append(step)

    def before_final(self):
        self.final.append('before')

    def after_final(self):
        self.final.append('after')


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert torch.empty(0).device.type == 'cpu'
        helper.configure_numeric(torch)
        cls.f = make_fixture()

    def test_01_all_parent_evidence_preserved(self):
        review = json.loads((BASE / 'training_readiness_joint_review_20261025_v1.json').read_text(encoding='utf-8'))
        for record in review['evidence_manifest']:
            self.assertEqual(c.sha(record['path']), record['sha256'])

    def test_02_static_sources_and_frozen_unchanged_model_bindings(self):
        for name in ('bcsp_training_contract_v1.py', 'bcsp_training_runtime_v5.py', 'bcsp_training_entry_v1.py'):
            ast.parse((HERE / name).read_text(encoding='utf-8'))
        self.assertEqual(entry.CONTRACT_SHA, c.sha(HERE / 'bcsp_training_contract_v1.py'))
        self.assertEqual(entry.PREFLIGHT_SHA, c.sha(BASE / 'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'))

    def test_03_qualified_QC_positive_and_limits_retained(self):
        selected, fold = c.verify_qualified_receipt(self.f.qualified, self.f.verification, self.f.manifests,
                                                   self.f.folds, 'C', 8192)
        self.assertEqual(len(selected), 315)
        self.assertEqual(len(fold['train_sources']), 63)
        self.assertEqual(self.f.qualified['limitations'], list(c.LIMITS))
        self.assertFalse(self.f.qualified['payload_reverified_by_this_mapping'])

    def test_04_unqualified_PASS_and_erased_limit_rejected(self):
        bad = c.json_bound(self.f.verification)
        bad['status'] = 'PASS'
        with self.assertRaisesRegex(ValueError, 'qualified QC'):
            c.bind_metadata(write('bad_QC_status.json', bad), self.f.manifests, self.f.folds, 'C', 8192)
        wrong = copy.deepcopy(self.f.qualified)
        wrong['limitations'] = []
        with self.assertRaises(ValueError):
            c.verify_qualified_receipt(wrong, self.f.verification, self.f.manifests, self.f.folds, 'C', 8192)

    def test_05_paired_target_drift_rejected(self):
        p = FIX / 'bad_target_manifest.jsonl'
        values = [json.loads(x) for x in Path(self.f.manifests['16384']['path']).read_text().splitlines()]
        values[0]['target_array_sha256'] = 'f' * 64
        with p.open('x', encoding='utf-8') as stream:
            for value in values:
                stream.write(json.dumps(value) + '\n')
        manifests = dict(self.f.manifests, **{'16384': binding(p)})
        qc = c.json_bound(self.f.verification)
        qc['important_file_hashes']['manifest_16384.jsonl'] = manifests['16384']['sha256']
        with self.assertRaisesRegex(ValueError, 'paired'):
            c.bind_metadata(write('bad_target_QC.json', qc), manifests, self.f.folds, 'C', 8192)

    def test_06_wrong_source_fold_rejected(self):
        folds = c.json_bound(self.f.folds)
        folds['folds']['C']['train_sources'][0] = 'OUTSIDE'
        with self.assertRaisesRegex(ValueError, 'source not train'):
            c.bind_metadata(self.f.verification, self.f.manifests, write('bad_source_fold.json', folds), 'C', 8192)

    def test_07_single_direction_authorization_positive(self):
        q, static = c.authorize(self.f.req, self.f.auth, self.f.runtime)
        self.assertEqual(q['static_config'], self.f.request['static_config'])
        self.assertEqual(static['counts']['updates'], 3900)
        self.assertNotIn('bcsp_execution', static)

    def test_08_reverse_bindings_or_recursive_static_config_rejected(self):
        auth = c.json_bound(self.f.auth)
        auth['runtime_sha256'] = self.f.runtime['sha256']
        with self.assertRaisesRegex(ValueError, 'reverse binding'):
            c.authorize(self.f.req, write('bad_reverse_auth.json', auth), self.f.runtime)
        config = copy.deepcopy(self.f.config)
        config['bcsp_execution'] = {'request_sha256': self.f.req['sha256']}
        with self.assertRaisesRegex(ValueError, 'static fields'):
            c.validate_static(config)

    def test_09_hash_drift_and_missing_authorization_rejected(self):
        req = dict(self.f.req, sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'drift'):
            c.authorize(req, self.f.auth, self.f.runtime)
        auth = c.json_bound(self.f.auth)
        auth['explicit_user_authorization'] = False
        with self.assertRaises(ValueError):
            c.authorize(self.f.req, write('bad_unauthorized.json', auth), self.f.runtime)

    def test_10_boolean_GPU_or_implicit_resource_budget_rejected(self):
        with self.assertRaises(ValueError):
            c.json_bound(True)
        for key in ('wall_seconds', 'output_bytes'):
            config = copy.deepcopy(self.f.config)
            config['resources'][key] = None
            with self.assertRaisesRegex(ValueError, 'explicit positive'):
                c.validate_static(config)

    def test_11_numeric_strict_settings_and_TF32_failure(self):
        helper.configure_numeric(torch)
        helper.assert_numeric(torch)
        try:
            torch.backends.cuda.matmul.allow_tf32 = True
            with self.assertRaises(RuntimeError):
                helper.assert_numeric(torch)
        finally:
            helper.configure_numeric(torch)

    def test_12_shared_order_matches_prior_loader_permutations(self):
        ids = self.f.plan['case_ids']
        self.assertEqual(r.make_order(ids), self.f.plan)
        source = ast.parse((BASE / 'implementation_candidate_v4/overlay/tools/bcsp_runtime.py').read_text())
        fn = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'make_loader')
        ns = {'torch': torch, 'DataLoader': DataLoader}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'parent_make_loader', 'exec'), ns)
        for epoch in (0, 1, 99):
            old = [batch.tolist() for batch in ns['make_loader'](list(range(315)), epoch)]
            self.assertEqual([[ids[i] for i in batch] for batch in old], self.f.plan['epochs'][epoch]['batches'])

    def test_13_duplicate_or_missing_order_rejected(self):
        plan = copy.deepcopy(self.f.plan)
        plan['epochs'][0]['dropped'][0] = plan['epochs'][0]['batches'][0][0]
        with self.assertRaises(ValueError):
            c.validate_order(plan, self.f.plan['case_ids'])

    def test_14_real_artificial_NPZ_dataset_shapes_and_identity(self):
        for n in (8192, 16384):
            root = FIX / ('array_%d' % n)
            (root / 'points').mkdir(parents=True)
            records = copy.deepcopy(c.bind_metadata(self.f.verification, self.f.manifests,
                                                    self.f.folds, 'C', n)[1])
            p = root / records[0]['point_path']
            np.savez(p, partial=np.zeros((n, 3), np.float32), implant=np.ones((8192, 3), np.float32))
            records[0]['sha256'] = c.sha(p)
            data = r.BCSPDataset(root, records, self.f.fold['train_sources'], n)
            x, y, cid, source = data[0]
            self.assertEqual((tuple(x.shape), tuple(y.shape)), ((n, 3), (8192, 3)))
            self.assertEqual((cid, source), (records[0]['case_id'], records[0]['source_id']))
            self.assertEqual(x.dtype, torch.float32)

    def test_15_dataset_counts_and_link_guard(self):
        with self.assertRaises(ValueError):
            r.BCSPDataset(FIX, self.f.selected[:-1], self.f.fold['train_sources'], 8192)
        target = (FIX / 'LINK_FIXTURE').absolute()
        with patch.object(Path, 'is_symlink', lambda self: self == target):
            with self.assertRaisesRegex(ValueError, 'linked'):
                c.no_links(target)

    def test_16_exact_315_payload_policy_and_checkpoint_boundary(self):
        root = FIX / 'policy16'
        out = FIX / 'owned16'
        paths = entry.payload_paths(root, self.f.selected)
        policy = entry.make_training_policy(helper, [root], out, paths)
        allowed = next(iter(paths))
        policy.check(allowed)
        policy.check(out / 'ckpt-last.pth', True)
        for path, write_flag in ((allowed, True), (root / 'dev.npz', False), (root / 'old.pth', False),
                                 (out / 'ckpt-other.pth', True), (root / '.env', False)):
            with self.assertRaises((ValueError, RuntimeError)):
                policy.check(path, write_flag)

    def test_17_process_and_network_guards_remain(self):
        policy = entry.make_training_policy(helper, [FIX], FIX / 'owned17', {})
        with self.assertRaises(RuntimeError):
            policy.audit('subprocess.Popen', ('fc-list', ['fc-list', '--help'], None, None))
        with self.assertRaises(RuntimeError):
            policy.audit('socket.connect', ())

    def test_18_namespace_skips_initializers_and_rejects_unbound_import(self):
        root = FIX / 'namespace18'
        for name in ('models', 'tools'):
            (root / name).mkdir(parents=True)
            (root / name / '__init__.py').write_text("raise AssertionError('MUST_NOT_EXECUTE')\n")
        module = root / 'models/artificial.py'
        module.write_text('CPU_FIXTURE_VALUE = 18\n')
        records = {'models/artificial.py': {'sha256': c.sha(module), 'bytes': module.stat().st_size}}
        with patch.dict(sys.modules):
            for name in list(sys.modules):
                if name.split('.')[0] in helper.PREFIXES:
                    del sys.modules[name]
            helper.namespace_packages(root)
            with patch.object(sys, 'meta_path', [helper.FiniteProjectImports(root, records)] + sys.meta_path):
                self.assertEqual(importlib.import_module('models.artificial').CPU_FIXTURE_VALUE, 18)
                with self.assertRaises(RuntimeError):
                    importlib.import_module('models.NOT_BOUND')

    def test_19_external_timeout_and_artificial_resource_sample(self):
        entry.verify_timeout(3600, ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '3600s', 'python'])
        with self.assertRaises(ValueError):
            entry.verify_timeout(3600, ['python'])
        cuda = types.SimpleNamespace(reset_peak_memory_stats=lambda _: None, synchronize=lambda: None,
                                     max_memory_allocated=lambda _: 100, max_memory_reserved=lambda _: 200)
        helper_fixture = types.SimpleNamespace(smi=lambda key, compute=False: [str(os.getpid())] if compute else ['100'])
        out = FIX / 'resource19'
        out.mkdir()
        budget = entry.TrainingBudget(self.f.config['resources'], out, types.SimpleNamespace(cuda=cuda), helper_fixture)
        with patch.object(budget, 'local', return_value=(123, 456)):
            budget.after_step(1)
        stored = json.loads((out / 'resources.jsonl').read_text())
        self.assertEqual((stored['committed_step'], stored['peak_reserved']), (1, 200))

    def test_20_resource_overrun_stops_no_success_record(self):
        cuda = types.SimpleNamespace(reset_peak_memory_stats=lambda _: None, synchronize=lambda: None,
                                     max_memory_allocated=lambda _: 21 * 1024**3, max_memory_reserved=lambda _: 200)
        out = FIX / 'resource20'
        out.mkdir()
        helper_fixture = types.SimpleNamespace(smi=lambda key, compute=False: [] if compute else ['100'])
        budget = entry.TrainingBudget(self.f.config['resources'], out, types.SimpleNamespace(cuda=cuda), helper_fixture)
        with patch.object(budget, 'local', return_value=(123, 456)):
            with self.assertRaisesRegex(ValueError, 'GPU/other-process'):
                budget.after_step(1)
        self.assertEqual((out / 'resources.jsonl').stat().st_size, 0)

    def test_21_actual_CPU_3900_step_lifecycle_logs_and_BN(self):
        torch.manual_seed(0)
        model = Tiny()
        before = model.linear.weight.detach().clone()
        budget = CPUResourceFixture()
        observed = []
        original = r.make_optimizer
        def optimizer(m):
            opt = original(m)
            opt.register_step_post_hook(lambda *args: observed.append(1))
            return opt
        with patch.object(r, 'make_optimizer', side_effect=optimizer):
            receipt = r.train_lifecycle(model, lambda e: TensorBatches(self.f.plan, e, self.f.selected),
                                        self.f.selected, self.f.plan, FIX / 'tiny_success', device='cpu',
                                        numeric_check=helper.assert_numeric, resources=budget, knn_enable=lambda: None,
                                        state_fingerprint=helper.state_sha)
        self.assertEqual(len(observed), 3900)
        self.assertEqual((receipt['optimizer_updates'], receipt['traversals'], receipt['case_exposures']), (3900, 100, 31200))
        self.assertFalse(torch.equal(before, model.linear.weight.detach()))
        self.assertEqual(model.bn.num_batches_tracked.item(), 3900)
        self.assertTrue(model.bn.track_running_stats)
        self.assertEqual((len(budget.before), len(budget.after), budget.final), (3900, 3900, ['before', 'after']))
        out = FIX / 'tiny_success'
        events = [json.loads(x) for x in (out / 'metrics.jsonl').read_text().splitlines()]
        self.assertEqual(len(events), 3900)
        self.assertEqual(events[0]['case_ids'], self.f.plan['epochs'][0]['batches'][0])
        self.assertEqual((events[-1]['epoch'], events[-1]['step']), (99, 3900))
        exposure = json.loads((out / 'exposure.json').read_text())
        self.assertEqual(sum(exposure['case'].values()), 31200)
        self.assertEqual(sum(exposure['dropped_case'].values()), 300)
        state = torch.load(out / 'ckpt-last.pth', weights_only=True, map_location='cpu')
        self.assertEqual(state['scheduler']['last_epoch'], 100)
        self.assertTrue(all(int(v['step']) == 3900 for v in state['optimizer']['state'].values()))

    def test_22_nonfinite_loss_stops_without_final_checkpoint(self):
        class Bad(Tiny):
            def get_loss(self, *args, **kwargs):
                return self.linear.weight.sum() * float('nan'), self.linear.weight.sum()
        out = FIX / 'tiny_nan'
        with self.assertRaisesRegex(ValueError, 'finite scalar loss'):
            r.train_lifecycle(Bad(), lambda e: TensorBatches(self.f.plan, e, self.f.selected), self.f.selected,
                              self.f.plan, out, device='cpu', numeric_check=helper.assert_numeric,
                              resources=CPUResourceFixture(), knn_enable=lambda: None,
                              state_fingerprint=helper.state_sha)
        self.assertEqual(json.loads((out / 'failure.json').read_text())['committed_steps'], 0)
        self.assertFalse((out / 'ckpt-last.pth').exists())

    def test_23_optimizer_failure_and_order_drift_stop(self):
        original = r.make_optimizer
        def fail_optimizer(m):
            opt = original(m)
            def stop(*args):
                raise RuntimeError('ARTIFICIAL_OPTIMIZER_FAILURE')
            opt.register_step_pre_hook(stop)
            return opt
        out = FIX / 'tiny_optimizer_failure'
        with patch.object(r, 'make_optimizer', side_effect=fail_optimizer):
            with self.assertRaisesRegex(RuntimeError, 'ARTIFICIAL_OPTIMIZER_FAILURE'):
                r.train_lifecycle(Tiny(), lambda e: TensorBatches(self.f.plan, e, self.f.selected), self.f.selected,
                                  self.f.plan, out, device='cpu', numeric_check=helper.assert_numeric,
                                  resources=CPUResourceFixture(), knn_enable=lambda: None,
                                  state_fingerprint=helper.state_sha)
        self.assertEqual(json.loads((out / 'failure.json').read_text())['committed_steps'], 0)
        with self.assertRaisesRegex(ValueError, 'actual batch/order drift'):
            r.train_lifecycle(Tiny(), lambda e: TensorBatches(self.f.plan, e, self.f.selected, True), self.f.selected,
                              self.f.plan, FIX / 'tiny_order_failure', device='cpu', numeric_check=helper.assert_numeric,
                              resources=CPUResourceFixture(), knn_enable=lambda: None,
                              state_fingerprint=helper.state_sha)

    def test_24_existing_output_refused_and_entry_fails_before_GPU(self):
        out = FIX / 'existing24'
        out.mkdir()
        (out / 'keep.txt').write_text('RETAIN')
        with self.assertRaises(ValueError):
            r.claim_output(out)
        argv = ['entry', '--request', self.f.req['path'], '--request-sha256', self.f.req['sha256'],
                '--authorization', self.f.auth['path'], '--authorization-sha256', self.f.auth['sha256'],
                '--runtime', self.f.runtime['path'], '--runtime-sha256', self.f.runtime['sha256']]
        with patch.object(sys, 'argv', argv), patch.object(torch.cuda, 'is_available', side_effect=AssertionError('NO_GPU')) as cuda:
            with self.assertRaisesRegex(ValueError, 'Linux -I -S -B'):
                entry.main()
        cuda.assert_not_called()
        self.test_01_all_parent_evidence_preserved()


if __name__ == '__main__':
    assert not OUT.exists(), 'one retained attempt; never repair/retry or clean up'
    FIX.mkdir(parents=True)
    inputs = [HERE / n for n in ('bcsp_training_contract_v1.py', 'bcsp_training_runtime_v5.py',
                                 'bcsp_training_entry_v1.py', 'test_training_closure_v1.py')]
    identities = [binding(p) for p in inputs]
    c.emit(OUT / 'attempt_started.json', {'attempts': 1, 'CPU_only': True, 'inputs': identities})
    with (OUT / 'cpu_contract_log.txt').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    receipt = {'status': 'PASS_ARTIFICIAL_CPU_ONLY' if result.wasSuccessful() else 'FAILED_STOP_NO_RETRY',
               'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'skips': len(result.skipped), 'attempts': 1, 'inputs': identities,
               'torch': torch.__version__, 'numpy': np.__version__, 'python': sys.version,
               'server_operations': 0, 'GPU_calls': 0, 'real_model_calls': 0, 'real_payload_reads': 0,
               'fixture_checkpoints': 'Only newly produced artificial Tiny CPU checkpoint; not research weights',
               'limits': ['No actual Linux training entry or actual GPU optimizer/BN memory test',
                          'Synthetic QC/auth/request fixtures cannot satisfy production pinned evidence hashes',
                          'Artificial 3900-step loop uses tiny 8x2x3 tensors; actual 8k/16k Dataset tested separately',
                          'Per-step resource monitoring is cooperative; external timeout remains mandatory']}
    c.emit(OUT / 'result.json', receipt)
    print(json.dumps(receipt))
    sys.exit(0 if result.wasSuccessful() else 1)
