"""One retained, fail-fast CPU batch. No server, native provider, model or CUDA call."""
import ast
import builtins
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import sys
import types
import unittest
from unittest.mock import patch

assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'explicitly hide CUDA before imports'
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OLD = HERE.parent / 'gpu_preflight_implementation_v1'
PARENT_MISC = PROJECT / 'outputs/cranial_scqr_v12_qa_github_publish_20261019/utils/misc.py'
CANDIDATE = HERE / 'overlay/utils/misc.py'
SCOPE = HERE / 'artificial_gpu_zero_update_frozen_scope_v3.json'
ENTRY = HERE / 'bcsp_artificial_gpu_preflight_v3.py'
ATTEMPT = HERE / 'cpu_attempt_v1'
PLOT_NAMES = {'get_ptcloud_img', 'visualize_KITTI'}
PLOT_ROOTS = {'matplotlib', 'mpl_toolkits'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(path):
    return ast.parse(Path(path).read_text(encoding='utf-8'))


def plotting_import(node):
    if isinstance(node, ast.Import):
        return any(a.name.split('.')[0] in PLOT_ROOTS for a in node.names)
    return isinstance(node, ast.ImportFrom) and node.module.split('.')[0] in PLOT_ROOTS


def load_entry():
    spec = importlib.util.spec_from_file_location('lazy_preflight_contract_entry', ENTRY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlotImportDenied(RuntimeError):
    pass


@contextlib.contextmanager
def deny_plot_imports():
    original = builtins.__import__
    seen = []

    def blocked(name, *args, **kwargs):
        if name.split('.')[0] in PLOT_ROOTS:
            seen.append(name)
            raise PlotImportDenied(name)
        return original(name, *args, **kwargs)

    with patch.object(builtins, '__import__', side_effect=blocked):
        yield seen


def load_misc(parent_oracle=False, provider=None):
    # Provider is a CPU routing fixture, not an implementation of native PointNet2.
    utils = types.ModuleType('utils')
    utils.__path__ = []
    provider = provider or types.ModuleType('utils.pointnet2_utils')
    utils.pointnet2_utils = provider
    source = (PARENT_MISC if parent_oracle else CANDIDATE).read_text(encoding='utf-8')
    if parent_oracle:
        source = source.replace('import matplotlib.pyplot as plt\n', '')
        source = source.replace('from mpl_toolkits.mplot3d import Axes3D\n', '')
    module = types.ModuleType('cpu_fixture_parent' if parent_oracle else 'cpu_fixture_candidate')
    with patch.dict(sys.modules, {'utils': utils, 'utils.pointnet2_utils': provider}):
        exec(compile(source, str(CANDIDATE), 'exec'), module.__dict__)
    return module


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert torch.empty(0).device.type == 'cpu'
        torch.set_num_threads(2)
        cls.scope = json.loads(SCOPE.read_text(encoding='utf-8'))
        cls.parent_scope = json.loads((HERE.parent / 'gpu_preflight_scope_v2/artificial_gpu_zero_update_frozen_scope_v2.json').read_text())
        cls.entry = load_entry()

    def test_01_parent_identity_and_all_finite_source_bindings(self):
        self.assertEqual(digest(PARENT_MISC), '65338858a2f2f87cc6040a7525a57beff26f0acc665caaedfb18bae5ab3d1a87')
        self.assertEqual(digest(OLD / 'bcsp_artificial_gpu_preflight_v2.py'), '347cc350454143b17bc4d8033b2c685b5665076a020058d05f8d87f416586da4')
        self.assertEqual(digest(SCOPE), self.entry.SCOPE_SHA)
        records = self.entry.source_map(self.scope)
        self.assertEqual(len(records), 18)
        for record in records.values():
            self.entry.exact(record['path'], record['sha256'], record['bytes'])
        config = self.scope['bindings']['base_config']
        self.entry.exact(config['path'], config['sha256'], config['bytes'])

    def test_02_complete_misc_AST_identical_except_import_relocation(self):
        parent, candidate = tree(PARENT_MISC), tree(CANDIDATE)
        parent.body = [n for n in parent.body if not plotting_import(n)]
        for node in candidate.body:
            if isinstance(node, ast.FunctionDef) and node.name in PLOT_NAMES:
                node.body = [n for n in node.body if not plotting_import(n)]
        self.assertEqual(ast.dump(parent, include_attributes=False), ast.dump(candidate, include_attributes=False))

    def test_03_only_two_plot_functions_have_local_plot_imports(self):
        module = tree(CANDIDATE)
        self.assertFalse(any(plotting_import(n) for n in module.body))
        found = {}
        for function in module.body:
            if isinstance(function, ast.FunctionDef):
                imports = [n for n in ast.walk(function) if plotting_import(n)]
                if imports:
                    found[function.name] = imports
        self.assertEqual(set(found), PLOT_NAMES)
        for name, imports in found.items():
            self.assertEqual(len(imports), 2, name)
            function = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
            self.assertTrue(all(plotting_import(n) for n in function.body[:2]))

    def test_04_normal_import_has_no_plot_subprocess_or_RNG_side_effect(self):
        py_state, np_state, torch_state = random.getstate(), np.random.get_state(), torch.get_rng_state().clone()
        before = {n for n in sys.modules if n.split('.')[0] in PLOT_ROOTS}
        with deny_plot_imports() as seen, patch('subprocess.Popen', side_effect=AssertionError('no subprocess')) as child:
            module = load_misc()
        child.assert_not_called()
        self.assertEqual(seen, [])
        self.assertTrue(callable(module.fps))
        self.assertEqual(before, {n for n in sys.modules if n.split('.')[0] in PLOT_ROOTS})
        self.assertEqual(py_state, random.getstate())
        after = np.random.get_state()
        self.assertEqual(np_state[0], after[0])
        np.testing.assert_array_equal(np_state[1], after[1])
        self.assertEqual(np_state[2:], after[2:])
        self.assertTrue(torch.equal(torch_state, torch.get_rng_state()))

    def test_05_FPS_real_CPU_tensor_routing_shape_dtype_and_RNG(self):
        calls = []
        provider = types.ModuleType('utils.pointnet2_utils')

        def sample(data, count):
            calls.append(('fps', tuple(data.shape), count, data.dtype, data.is_contiguous()))
            return torch.arange(count, dtype=torch.int32).expand(data.shape[0], -1).contiguous()

        def gather(data, indices):
            calls.append(('gather', tuple(data.shape), tuple(indices.shape), data.dtype, data.is_contiguous()))
            return data.gather(2, indices.long().unsqueeze(1).expand(-1, data.shape[1], -1))

        provider.furthest_point_sample, provider.gather_operation = sample, gather
        with deny_plot_imports() as seen:
            candidate, parent = load_misc(provider=provider), load_misc(True, provider)
            for n in (17, 33):
                data = torch.arange(2 * n * 3, dtype=torch.float32).reshape(2, n, 3)
                state = torch.get_rng_state().clone()
                calls.clear()
                actual = candidate.fps(data, 7)
                candidate_calls = copy.deepcopy(calls)
                calls.clear()
                expected = parent.fps(data, 7)
                self.assertEqual(candidate_calls, calls)
                self.assertTrue(torch.equal(actual, expected))
                self.assertTrue(torch.equal(actual, data[:, :7]))
                self.assertEqual(actual.shape, (2, 7, 3))
                self.assertEqual(actual.dtype, torch.float32)
                self.assertTrue(torch.equal(state, torch.get_rng_state()))
        self.assertEqual(seen, [])

    def test_06_jitter_exact_parent_CPU_output_and_RNG_parity(self):
        with deny_plot_imports() as seen:
            candidate, parent = load_misc(), load_misc(True)
            state = torch.get_rng_state().clone()
            expected = parent.jitter_points(torch.zeros(2, 17, 3))
            after = torch.get_rng_state().clone()
            torch.set_rng_state(state)
            actual = candidate.jitter_points(torch.zeros(2, 17, 3))
            self.assertTrue(torch.equal(expected, actual))
            self.assertTrue(torch.equal(after, torch.get_rng_state()))
            torch.set_rng_state(state)
        self.assertEqual(seen, [])

    def test_07_plot_image_import_is_deferred_until_explicit_call(self):
        module = load_misc()
        with deny_plot_imports() as seen:
            with self.assertRaises(PlotImportDenied):
                module.get_ptcloud_img(None)
        self.assertEqual(seen, ['matplotlib.pyplot'])

    def test_08_plot_KITTI_import_is_deferred_before_any_output(self):
        module = load_misc()
        with deny_plot_imports() as seen, patch.object(os, 'makedirs', side_effect=AssertionError('no output')) as write:
            with self.assertRaises(PlotImportDenied):
                module.visualize_KITTI('UNUSED_CPU_SENTINEL', [])
        write.assert_not_called()
        self.assertEqual(seen, ['matplotlib.pyplot'])

    def test_09_entire_entry_AST_unchanged_except_scope_hash(self):
        parent, candidate = tree(OLD / 'bcsp_artificial_gpu_preflight_v2.py'), tree(ENTRY)
        for module in (parent, candidate):
            module.body = [n for n in module.body if not (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCOPE_SHA' for t in n.targets))]
        self.assertEqual(ast.dump(parent, include_attributes=False), ast.dump(candidate, include_attributes=False))

    def test_10_scientific_provider_monitor_contracts_and_other_bindings_unchanged(self):
        for key in ('identity', 'model', 'input', 'operations', 'loss_backend', 'numerical', 'state_protection', 'knn_oracle', 'resources', 'environment', 'monitoring_v2', 'materialization'):
            self.assertEqual(self.scope[key], self.parent_scope[key], key)
        actual = copy.deepcopy(self.scope['bindings'])
        previous = copy.deepcopy(self.parent_scope['bindings'])
        for bindings in (actual, previous):
            bindings['isolated_model_project_sources'] = [r for r in bindings['isolated_model_project_sources'] if r['relative_path'] != 'utils/misc.py']
        self.assertEqual(actual, previous)
        self.assertEqual(self.scope['isolation']['future_root'], self.parent_scope['isolation']['future_root'].replace('_v2', '_v3'))
        self.assertEqual(self.scope['filesystem']['future_output'], self.parent_scope['filesystem']['future_output'].replace('_v2', '_v3'))
        self.assertEqual(self.scope['filesystem']['future_tmux_session'], self.parent_scope['filesystem']['future_tmux_session'].replace('_v2', '_v3'))

    def test_11_process_network_payload_secret_and_write_guards_still_reject(self):
        policy = self.entry.FilePolicy([ATTEMPT], ATTEMPT / 'owned')
        for command in (['fc-list', '--help'], ['fc-list', '--format=%{file}'], ['/usr/bin/fc-list', '--help']):
            with self.assertRaisesRegex(RuntimeError, 'only fixed read-only'):
                policy.audit('subprocess.Popen', (command[0], command, None, None))
        for name in ('skull.npz', 'model.pth', '.env'):
            with self.assertRaises(RuntimeError):
                policy.check(ATTEMPT / name)
        with self.assertRaises(RuntimeError):
            policy.check(ATTEMPT / 'outside-owned.txt', True)
        for event in ('socket.connect', 'os.system', 'os.exec', 'os.posix_spawn'):
            with self.assertRaises(RuntimeError):
                policy.audit(event, ())

    def test_12_model_source_retains_unconditional_FPS_and_no_plot_calls(self):
        record = next(r for r in self.scope['bindings']['isolated_model_project_sources'] if r['relative_path'] == 'models/AdaPoinTr.py')
        module = tree(record['path'])
        cls = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'PCTransformer')
        forward = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'forward')
        direct = [n for n in forward.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and isinstance(n.value.func.value, ast.Name) and n.value.func.value.id == 'misc' and n.value.func.attr == 'fps']
        self.assertTrue(direct, 'FPS must remain directly in forward, not removed for learned_only')
        self.assertFalse(any(isinstance(n, ast.Attribute) and n.attr in PLOT_NAMES for n in ast.walk(module)))


if __name__ == '__main__':
    assert not ATTEMPT.exists(), 'one consumed attempt; no retry or cleanup'
    ATTEMPT.mkdir()
    identity = {'entry_sha256': digest(ENTRY), 'test_sha256': digest(__file__), 'misc_sha256': digest(CANDIDATE), 'scope_sha256': digest(SCOPE)}
    with (ATTEMPT / 'attempt_started.json').open('x', encoding='utf-8') as stream:
        json.dump({'attempts': 1, 'CPU_only': True, **identity}, stream, indent=2)
    with (ATTEMPT / 'cpu_contract_log.txt').open('x', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contracts))
    receipt = {'status': 'PASS' if result.wasSuccessful() else 'FAIL_STOP_NO_RETRY', 'tests_run': result.testsRun, 'errors': len(result.errors), 'failures': len(result.failures), 'attempts': 1, 'torch': torch.__version__, 'numpy': np.__version__, 'server_operations': 0, 'GPU_operations': 0, 'model_forwards': 0, 'native_provider_calls': 0, 'fc_list_calls': 0, 'fixtures_retained': True, **identity}
    with (ATTEMPT / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt))
    sys.exit(0 if result.wasSuccessful() else 1)
