"""One fail-fast CPU batch; retained project fixtures; never imports real model."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import threading
import types
import unittest
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
FIXTURES = HERE / 'cpu_attempt_v3' / 'fixtures'
SCOPE = PROJECT / 'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_scope_v2/artificial_gpu_zero_update_frozen_scope_v2.json'
spec = importlib.util.spec_from_file_location('preflight', HERE / 'bcsp_artificial_gpu_preflight_v2.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
scope = p.read_json(p.exact(SCOPE, p.SCOPE_SHA))


def fixture(name, content):
    path = FIXTURES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    return path


def load_adapter():
    path = Path(scope['bindings']['candidate'][3]['path'])
    spec = importlib.util.spec_from_file_location('tools.bcsp_adapter', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def transformer_subset():
    path = Path(scope['bindings']['candidate'][1]['path'])
    tree = ast.parse(path.read_text(encoding='utf-8'))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {'knn_point', 'square_distance', 'enable_bcsp_knn'}]
    namespace = {'torch': torch, '_BCSP_KNN_ENABLED': False}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(path), 'exec'), namespace)
    # Preserve function globals and expose flag dynamically, as a real module would.
    class Proxy:
        def __getattr__(self, key):
            return namespace[key]
    return Proxy()


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.base_model = torch.nn.Module()
        self.base_model.grouper = torch.nn.Linear(3, 6)
        self.base_model.encoder = torch.nn.Linear(6, 6)
        self.base_model.decoder = torch.nn.Linear(6, 3)
        self.bn = torch.nn.BatchNorm1d(6)

    def forward(self, x):
        y = self.base_model.grouper(x.mean(1))
        y = self.base_model.encoder(self.bn(y)).tanh()
        y = self.base_model.decoder(y).unsqueeze(1)
        coarse, fine = y.expand(8, 256, 3), y.expand(8, 8192, 3)
        return coarse, coarse[:, :0], fine[:, :0], fine

    def get_loss(self, ret, target, epoch, partial):
        assert epoch == 0 and partial.shape[-1] == 3
        return ret[3].new_zeros(()), ((ret[3] - target) ** 2).mean() + ret[0].square().mean()


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '' and torch.empty(0).device.type == 'cpu',
                  'CPU execution required: CUDA hidden and default tensor device CPU')
        p.require(not FIXTURES.exists(), 'fresh retained fixture directory required')
        FIXTURES.mkdir(parents=True)
        p.configure_numeric(torch)

    def test_01_all_frozen_sources_unchanged(self):
        records = p.source_map(scope)
        self.assertEqual(len(records), 18)
        for record in records.values():
            p.exact(record['path'], record['sha256'], record['bytes'])
        p.exact(scope['bindings']['base_config']['path'], scope['bindings']['base_config']['sha256'])

    def test_02_exact_and_exclusive_artifacts(self):
        f = fixture('exact.txt', 'identity')
        p.exact(f, p.sha(f), 8)
        for digest, size in [('0' * 64, 8), (p.sha(f), 7)]:
            with self.assertRaises(RuntimeError):
                p.exact(f, digest, size)
        j = FIXTURES / 'exclusive.json'
        p.emit_new(j, {'ok': True})
        with self.assertRaises(FileExistsError):
            p.emit_new(j, {})
        output = FIXTURES / 'launcher_only'
        output.mkdir()
        (output / 'launch.log').write_text('', encoding='utf-8')
        p.claim_output(output)
        self.assertTrue((output / 'worker.pid').is_file())
        with self.assertRaises(RuntimeError):
            p.claim_output(output)

    def test_03_namespaces_do_not_execute_initializers(self):
        root = FIXTURES / 'namespace'
        fixture('namespace/models/__init__.py', 'raise RuntimeError("must not execute")')
        fixture('namespace/tools/__init__.py', 'raise RuntimeError("must not execute")')
        with patch.dict(sys.modules):
            for name in p.PREFIXES:
                sys.modules.pop(name, None)
            p.namespace_packages(root)
            self.assertEqual(sys.modules['models'].__path__, [str(root / 'models')])
            self.assertIsNone(sys.modules['tools'].__spec__.loader)

    def test_04_finite_import_gate(self):
        finder = p.FiniteProjectImports(FIXTURES, {})
        for name in ['tools.runner', 'tools.bcsp_runtime', 'models.unbound']:
            with self.assertRaises(RuntimeError):
                finder.find_spec(name)
        self.assertIsNone(finder.find_spec('numpy.data'))

    def test_05_policy_dependency_data_not_project_data(self):
        policy = p.FilePolicy([FIXTURES / 'env', FIXTURES / 'isolated'], FIXTURES / 'output')
        policy.check(FIXTURES / 'env/data/resource.txt')
        with self.assertRaises(RuntimeError):
            policy.check(FIXTURES / 'project/data/resource.txt')
        with self.assertRaises(RuntimeError):
            policy.check(FIXTURES / 'isolated/case.npz')

    def test_06_policy_writes_secrets_and_processes(self):
        policy = p.FilePolicy([FIXTURES], FIXTURES / 'owned')
        policy.check(FIXTURES / 'owned/log.txt', True)
        for path, write in [(FIXTURES / '.ssh/config', False), (FIXTURES / 'elsewhere.txt', True)]:
            with self.assertRaises(RuntimeError):
                policy.check(path, write)
        for event, args in [('socket.connect', ()), ('os.system', ('echo',)),
                            ('subprocess.Popen', ('python', ['python', '-c', 'pass']))]:
            with self.assertRaises(RuntimeError):
                policy.audit(event, args)

    def authorization_fixture(self, label):
        request = fixture(label + '/request.json', json.dumps({'status': 'AWAITING_EXPLICIT_USER_AUTHORIZATION',
                                                              'scope_sha256': p.SCOPE_SHA}))
        auth = fixture(label + '/auth.json', json.dumps({'schema': 'bcsp-preflight-authorization-v1',
                         'request_sha256': p.sha(request), 'explicit_user_authorization': True,
                         'user_authorization_text': 'ARTIFICIAL FIXTURE NOT REAL AUTHORIZATION'}))
        runtime = fixture(label + '/runtime.json', json.dumps({'schema': 'bcsp-preflight-runtime-v1',
                          'request_sha256': p.sha(request), 'authorization_sha256': p.sha(auth)}))
        return request, auth, runtime

    def test_07_single_direction_authorization(self):
        request, auth, runtime = self.authorization_fixture('auth7')
        self.assertEqual(p.authorize(request, p.sha(request), auth, runtime)['scope_sha256'], p.SCOPE_SHA)

    def test_08_authorization_mismatch_and_cycle_rejected(self):
        request, auth, runtime = self.authorization_fixture('auth8')
        with self.assertRaises(RuntimeError):
            p.authorize(request, '0' * 64, auth, runtime)
        data = p.read_json(auth)
        data['runtime_sha256'] = p.sha(runtime)
        auth.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(RuntimeError):
            p.authorize(request, p.sha(request), auth, runtime)

    def test_09_static_no_training_entry(self):
        tree = ast.parse((HERE / 'bcsp_artificial_gpu_preflight_v2.py').read_text(encoding='utf-8'))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertFalse(any('optim.' in c or c.endswith('.step') or 'torch.load' in c or 'torch.save' in c for c in calls))
        text = (HERE / 'bcsp_artificial_gpu_preflight_v2.py').read_text(encoding='utf-8')
        self.assertIn("['model']", text)
        self.assertIn("'request', 'request-sha256', 'authorization', 'runtime', 'scope'", text)

    def test_10_numeric_contract(self):
        p.assert_numeric(torch)
        torch.backends.cudnn.benchmark = True
        try:
            with self.assertRaises(RuntimeError):
                p.assert_numeric(torch)
        finally:
            torch.backends.cudnn.benchmark = False

    def test_11_tensor_bytes_no_numpy_bridge(self):
        for tensor in [torch.tensor(7), torch.empty(0), torch.arange(12.).view(3, 4).T]:
            self.assertEqual(p.tensor_sha(tensor), p.tensor_sha(tensor.clone()))
        self.assertNotEqual(p.tensor_sha(torch.tensor(7)), p.tensor_sha(torch.tensor(8)))

    def test_12_training_bn_without_running_writes(self):
        model = torch.nn.Sequential(torch.nn.BatchNorm1d(4), torch.nn.Linear(4, 1)).eval()
        evidence = {}
        with p.no_update(torch, model, evidence):
            self.assertTrue(model[0].training)
            self.assertFalse(model[0].track_running_stats)
            model(torch.arange(32.).view(8, 4)).square().mean().backward()
            self.assertIsNotNone(model[1].weight.grad)
        self.assertTrue(evidence['flags_restored'] and evidence['bn_tracking_restored'])
        self.assertEqual(evidence['state_before'], evidence['state_after'])
        self.assertTrue(all(x.grad is None for x in model.parameters()))

    def test_13_exception_restores_bn_flags(self):
        model = torch.nn.BatchNorm1d(3).eval()
        with self.assertRaisesRegex(ValueError, 'fixture stop'):
            with p.no_update(torch, model, {}):
                raise ValueError('fixture stop')
        self.assertFalse(model.training)
        self.assertTrue(model.track_running_stats)

    def test_14_state_mutation_detected_not_undone(self):
        model = torch.nn.Linear(3, 1)
        before = p.state_sha(model)
        with self.assertRaisesRegex(RuntimeError, 'state changed'):
            with p.no_update(torch, model, {}):
                with torch.no_grad():
                    model.weight.add_(1)
        self.assertNotEqual(before, p.state_sha(model))

    def test_15_rng_restored(self):
        before = torch.get_rng_state().clone()
        evidence = {}
        with p.rng_preserved(torch, np, evidence=evidence):
            random.random()
            np.random.random()
            torch.rand(12)
        self.assertTrue(torch.equal(before, torch.get_rng_state()))
        self.assertTrue(evidence['rng_restored'])

    def test_16_exception_restores_rng(self):
        before = torch.get_rng_state().clone()
        with self.assertRaises(ValueError):
            with p.rng_preserved(torch, np):
                torch.manual_seed(98)
                raise ValueError('stop')
        self.assertTrue(torch.equal(before, torch.get_rng_state()))

    def test_17_synthetic_shape_prefix_common_target(self):
        x, y = p.synthetic(np, torch)
        again, target = p.synthetic(np, torch)
        self.assertEqual(tuple(x.shape), (8, 16384, 3))
        self.assertEqual(tuple(y.shape), (8, 8192, 3))
        self.assertEqual(x.dtype, torch.float32)
        self.assertTrue(torch.equal(x[:, :8192], again[:, :8192]) and torch.equal(y, target))
        self.assertTrue(bool((x >= -.5).all() and (x <= .5).all()))

    def backend(self):
        names = ('furthest_point_sample', 'gather_operation', 'grouping_operation', 'three_nn', 'three_interpolate', 'ball_query')
        provider = types.SimpleNamespace(**{n: object() for n in names})
        adapter = types.SimpleNamespace(**vars(provider), using_fallback=lambda: False)
        return types.SimpleNamespace(chamfer=None), adapter, provider

    def test_18_native_provider_required(self):
        chamfer, adapter, provider = self.backend()
        p.check_backend(chamfer, adapter, provider)
        adapter.using_fallback = lambda: True
        with self.assertRaises(RuntimeError):
            p.check_backend(chamfer, adapter, provider)
        adapter.using_fallback = lambda: False
        adapter.gather_operation = object()
        with self.assertRaises(RuntimeError):
            p.check_backend(chamfer, adapter, provider)

    def test_19_compiled_chamfer_rejected(self):
        chamfer, adapter, provider = self.backend()
        chamfer.chamfer = object()
        with self.assertRaises(RuntimeError):
            p.check_backend(chamfer, adapter, provider)
        wrapper = next(r for r in scope['bindings']['isolated_model_project_sources']
                       if r['relative_path'] == 'extensions/chamfer_dist/__init__.py')
        spec = importlib.util.spec_from_file_location('cpu_chamfer_contract', wrapper['path'])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIsNone(module.chamfer)
        xyz = torch.arange(24., dtype=torch.float32).view(1, 8, 3).div(24).requires_grad_()
        target = torch.arange(33., dtype=torch.float32).view(1, 11, 3).div(37) + .01
        loss = module.ChamferDistanceL1()(xyz, target) + module.ChamferDistanceL1Directional()(xyz, target)
        loss.backward()
        self.assertTrue(bool(torch.isfinite(xyz.grad).all() and (xyz.grad != 0).any()))

    def oracle(self, n):
        load_adapter()
        transformer = transformer_subset()
        x, _ = p.synthetic(np, torch)
        result = p.knn_oracle(torch, np, transformer, x[:1, :n])
        self.assertEqual(result['chunks'], [256, 1])
        self.assertTrue(result['distance_comparison_pass'])

    def test_20_knn_8192_actual_candidate(self):
        self.oracle(8192)

    def test_21_knn_16384_actual_candidate(self):
        self.oracle(16384)

    def test_22_two_tiny_forward_loss_backward_zero_updates(self):
        master, target = p.synthetic(np, torch)
        counters = {'forward': 0, 'loss': 0, 'backward': 0}
        initial = []
        for n in (8192, 16384):
            with p.rng_preserved(torch, np):
                torch.manual_seed(0)
                model = Tiny().eval()
                initial.append(p.state_sha(model, True))
                evidence = {}
                p.model_step(torch, model, master[:, :n], target, counters, evidence)
                self.assertTrue(all(evidence['nonzero_gradient_parameters'].values()))
                self.assertEqual(evidence['state_before'], evidence['state_after'])
        self.assertEqual(initial[0], initial[1])
        self.assertEqual(counters, {'forward': 2, 'loss': 2, 'backward': 2})

    def test_23_fail_first_arm_structure(self):
        tree = ast.parse((HERE / 'bcsp_artificial_gpu_preflight_v2.py').read_text(encoding='utf-8'))
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        loop = next(n for n in ast.walk(run) if isinstance(n, ast.For) and ast.unparse(n.target) == 'n')
        self.assertEqual(ast.literal_eval(loop.iter), (8192, 16384))
        self.assertFalse(any(isinstance(n, ast.Try) for n in ast.walk(loop)))
        self.assertEqual(sum(isinstance(n, ast.Call) and ast.unparse(n.func) == 'model_step' for n in ast.walk(loop)), 1)

    def test_24_resource_budgets(self):
        budget = p.Budget(scope, FIXTURES)
        budget.check_values(1024, 0, 2048)
        limits = scope['resources']
        for rss, gpu, output in [(limits['process_RSS_monitored_limit_bytes'] + 1, 0, 0),
                                 (0, limits['device_memory_stop_MiB'] + 1, 0),
                                 (0, 0, limits['result_output_limit_bytes'] + 1)]:
            with self.assertRaises(RuntimeError):
                budget.check_values(rss, gpu, output)


class FakeQueryProcess:
    def __init__(self, out=b'42\n', err=b'', code=0, timeout_first=False, cleanup_timeout=False):
        self.pid, self.returncode = 4321, None
        self.out, self.err, self.code = out, err, code
        self.timeout_first, self.cleanup_timeout = timeout_first, cleanup_timeout
        self.communicate_timeouts, self.kill_calls = [], 0

    def communicate(self, timeout):
        self.communicate_timeouts.append(timeout)
        if (self.timeout_first and len(self.communicate_timeouts) == 1) or (
                self.cleanup_timeout and len(self.communicate_timeouts) == 2):
            raise subprocess.TimeoutExpired(['ARTIFICIAL_SMI'], timeout, output=self.out, stderr=self.err)
        if self.returncode is None:
            self.returncode = self.code
        return self.out, self.err

    def poll(self):
        return self.returncode

    def kill(self):
        self.kill_calls += 1
        self.returncode = -9


class MonitorContracts(Contracts):
    def budget(self, name):
        output = FIXTURES / name
        output.mkdir()
        return p.Budget(scope, output)

    def events(self, budget):
        return [json.loads(x) for x in budget.event_path.read_text(encoding='utf-8').splitlines()]

    def test_25_monitor_budget_and_science_frozen(self):
        old = p.read_json(PROJECT / 'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_scope_v1/artificial_gpu_zero_update_frozen_scope_v1.json')
        for key in ('resources', 'model', 'input', 'operations', 'loss_backend', 'numerical', 'state_protection', 'knn_oracle', 'bindings'):
            self.assertEqual(scope[key], old[key])
        self.assertEqual((p.SMI_TIMEOUT, p.SMI_REAP_TIMEOUT, p.MONITOR_POLL_WAIT), (10., 2., 2.))
        self.assertTrue(scope['monitoring_v2']['no_query_retries'])
        self.assertNotEqual(scope['filesystem']['future_output'], old['filesystem']['future_output'])
        self.assertNotEqual(scope['isolation']['future_root'], old['isolation']['future_root'])

    def test_26_success_actual_smi_argument_contract(self):
        budget = self.budget('monitor26')
        budget.phase('import:fixture')
        proc = FakeQueryProcess()
        with patch.object(p, '_MONITOR', budget), patch.object(p.subprocess, 'Popen', return_value=proc) as spawn:
            self.assertEqual(p.smi('memory.used'), ['42'])
        args = spawn.call_args[0][0]
        self.assertEqual(args[0], '/usr/bin/nvidia-smi')
        self.assertIn('--query-gpu=memory.used', args)
        self.assertEqual(proc.communicate_timeouts, [10.])
        result = self.events(budget)[-1]
        self.assertEqual((result['status'], result['child_pid'], result['returncode']), ('OK', 4321, 0))
        self.assertEqual(result['phase_at_start'], 'import:fixture')
        self.assertGreaterEqual(result['elapsed_seconds'], 0)

    def test_27_timeout_partial_output_bounded_and_one_attempt(self):
        budget = self.budget('monitor27')
        proc = FakeQueryProcess(out=b'x' * 3000, err=b'partial-error', timeout_first=True)
        factory = unittest.mock.Mock(return_value=proc)
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], 10., budget, _popen=factory)
        d = error.exception.details
        self.assertEqual(d['status'], 'TIMEOUT')
        self.assertEqual(d['exception_type'], 'TimeoutExpired')
        self.assertEqual(proc.communicate_timeouts, [10., 2.])
        self.assertEqual((factory.call_count, proc.kill_calls), (1, 1))
        self.assertTrue(d['cleanup_completed'] and d['stdout']['truncated'])
        self.assertEqual(d['stdout']['bytes_total'], 3000)
        self.assertEqual(len(d['stdout']['text'].encode()), 2048)
        self.assertEqual(d['stderr']['text'], 'partial-error')
        self.assertEqual(self.events(budget)[-1]['status'], 'TIMEOUT')

    def test_28_nonzero_query_exit_no_retry(self):
        proc = FakeQueryProcess(err=b'fixed artificial error', code=7)
        factory = unittest.mock.Mock(return_value=proc)
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], 10., _popen=factory)
        self.assertEqual(error.exception.details['status'], 'NONZERO_EXIT')
        self.assertEqual(error.exception.details['returncode'], 7)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(proc.kill_calls, 0)

    def test_29_spawn_failure_is_classified(self):
        factory = unittest.mock.Mock(side_effect=FileNotFoundError('ARTIFICIAL_MISSING_BINARY'))
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], 10., _popen=factory)
        self.assertEqual(error.exception.details['status'], 'QUERY_ERROR')
        self.assertEqual(error.exception.details['exception_type'], 'FileNotFoundError')
        self.assertIsNone(error.exception.details['child_pid'])
        self.assertEqual(factory.call_count, 1)

    def test_30_cleanup_timeout_still_stops_without_retry(self):
        proc = FakeQueryProcess(timeout_first=True, cleanup_timeout=True)
        factory = unittest.mock.Mock(return_value=proc)
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], 10., _popen=factory)
        d = error.exception.details
        self.assertEqual(d['status'], 'TIMEOUT')
        self.assertFalse(d['cleanup_completed'])
        self.assertEqual(d['cleanup_exception_type'], 'TimeoutExpired')
        self.assertEqual(proc.communicate_timeouts, [10., 2.])
        self.assertEqual((factory.call_count, proc.kill_calls), (1, 1))

    def test_31_phase_changes_are_recorded_during_query(self):
        budget = self.budget('monitor31')
        budget.phase('import:before')
        proc = FakeQueryProcess()
        original = proc.communicate
        def communicate(timeout):
            budget.phase('import:after')
            return original(timeout)
        proc.communicate = communicate
        p._smi_once(['/usr/bin/nvidia-smi'], 10., budget, _popen=lambda *a, **kw: proc)
        result = self.events(budget)[-1]
        self.assertEqual((result['phase_at_start'], result['phase_at_end']), ('import:before', 'import:after'))
        self.assertGreaterEqual(result['end_monotonic_ns'], result['start_monotonic_ns'])

    def test_32_failure_evidence_precedes_single_worker_stop(self):
        budget = self.budget('monitor32')
        details = {'status': 'TIMEOUT', 'exception_type': 'TimeoutExpired', 'child_pid': 4321}
        def termination(pid, sig):
            stored = p.read_json(budget.output / 'monitor_failure.json')
            self.assertEqual(stored['query_failure'], details)
            self.assertEqual(stored['exception_type'], 'MonitorQueryFailure')
            self.assertEqual((pid, sig), (os.getpid(), p.signal.SIGTERM))
        with patch.object(budget.stop, 'wait', return_value=False), \
             patch.object(budget, 'sample', side_effect=p.MonitorQueryFailure(details)) as sample, \
             patch.object(p.os, 'kill', side_effect=termination) as kill:
            budget.watch()
        self.assertEqual((sample.call_count, kill.call_count), (1, 1))

    def test_33_RSS_stop_is_checked_before_smi_wait(self):
        budget = self.budget('monitor33')
        rss_kb = scope['resources']['process_RSS_monitored_limit_bytes'] // 1024 + 1
        with patch.object(p.Path, 'read_text', return_value='VmRSS: ' + str(rss_kb) + ' kB\n'), \
             patch.object(p, 'smi') as query:
            with self.assertRaisesRegex(RuntimeError, 'RSS budget'):
                budget.sample()
        query.assert_not_called()

    def test_34_invalid_output_does_not_become_success(self):
        proc = FakeQueryProcess(out=b'\xff')
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], 10., _popen=lambda *a, **kw: proc)
        self.assertEqual(error.exception.details['status'], 'OUTPUT_DECODE_ERROR')
        self.assertEqual(error.exception.details['stdout']['bytes_total'], 1)
        self.assertEqual(proc.communicate_timeouts, [10.])

    def test_35_real_harmless_CPU_child_and_phase_thread(self):
        budget = self.budget('monitor35')
        budget.phase('artificial:before_spawn')
        ready, changed = threading.Event(), threading.Event()
        def phase_thread():
            if ready.wait(3):
                budget.phase('artificial:concurrent_phase')
                changed.set()
        thread = threading.Thread(target=phase_thread, daemon=True)
        thread.start()
        children = []
        def factory(args, **kwargs):
            self.assertEqual(args, ['/usr/bin/nvidia-smi'])
            child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c',
                                      "print('CPU_FIXTURE_ONLY',flush=True)"], **kwargs)
            children.append(child)
            ready.set()
            self.assertTrue(changed.wait(3))
            return child
        result = p._smi_once(['/usr/bin/nvidia-smi'], 3., budget, _popen=factory)
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(result, ['CPU_FIXTURE_ONLY'])
        self.assertEqual(children[0].returncode, 0)
        self.assertEqual(self.events(budget)[-1]['phase_at_end'], 'artificial:concurrent_phase')

    def test_36_real_harmless_CPU_child_timeout_reaped(self):
        budget = self.budget('monitor36')
        children = []
        def factory(args, **kwargs):
            child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c',
                                      'import time;time.sleep(5)'], **kwargs)
            children.append(child)
            return child
        with self.assertRaises(p.MonitorQueryFailure) as error:
            p._smi_once(['/usr/bin/nvidia-smi'], .2, budget, _popen=factory)
        self.assertEqual(error.exception.details['status'], 'TIMEOUT')
        self.assertTrue(error.exception.details['cleanup_completed'])
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())


if __name__ == '__main__':
    # A consumed attempt never gets replaced. No retries or automatic fixture cleanup.
    result_path = HERE / 'cpu_attempt_v3/result.json'
    p.require(not result_path.exists(), 'attempt already consumed')
    result_path.parent.mkdir(parents=True, exist_ok=True)
    p.emit_new(result_path.parent / 'attempt_started.json',
               {'attempts': 1, 'entry_sha256': p.sha(HERE / 'bcsp_artificial_gpu_preflight_v2.py'),
                'test_sha256': p.sha(__file__), 'CPU_only': True})
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MonitorContracts)
    with (result_path.parent / 'cpu_contract_log.txt').open('x', encoding='utf-8') as stream, \
         (result_path.parent / 'cpu_stdout.txt').open('x', encoding='utf-8') as stdout:
        with p.contextlib.redirect_stdout(stdout):
            result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True).run(suite)
    p.emit_new(result_path, {'schema': 'bcsp-preflight-cpu-contract-result-v1',
                            'status': 'PASS' if result.wasSuccessful() else 'FAIL_STOP_NO_RETRY',
                            'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                            'entry_sha256': p.sha(HERE / 'bcsp_artificial_gpu_preflight_v2.py'),
                            'test_sha256': p.sha(__file__), 'torch': torch.__version__, 'numpy': np.__version__,
                            'server_operations': 0, 'GPU_operations': 0, 'real_model_forwards': 0,
                            'real_payload_reads': 0, 'attempts': 1, 'fixtures_retained': str(FIXTURES)})
    print(json.dumps({'status': 'PASS' if result.wasSuccessful() else 'FAIL_STOP_NO_RETRY',
                      'tests_run': result.testsRun, 'result_path': str(result_path)}))
    sys.exit(0 if result.wasSuccessful() else 1)
