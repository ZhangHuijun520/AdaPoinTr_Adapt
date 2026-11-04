"""One new CPU attempt; fixture location/retention only, no test assertion edits."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
import uuid

BASE = Path(__file__).resolve().parent
OUT = BASE / 'cpu_tensor_attempt_v3'
FIXTURES = OUT / 'fixtures'
V2 = BASE / 'implementation_candidate_v2'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(name, obj):
    with (OUT / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

class RetainedFixtureDirectory:
    """Only replaces the two tests' TemporaryDirectory destination/cleanup."""
    def __init__(self, suffix=None, prefix=None, dir=None):
        if prefix not in {'bcsp_artificial_', 'bcsp_cpu_v2_artificial_'} or suffix is not None or dir is not None:
            raise ValueError('unexpected fixture directory contract')
        self.path = FIXTURES / (prefix + uuid.uuid4().hex)
        self.path.mkdir(exist_ok=False)
        self.name = str(self.path)
    def cleanup(self):
        # Intentionally retain artifacts, including fixtures from failed tests.
        return None
    def __enter__(self):
        return self.name
    def __exit__(self, *args):
        self.cleanup()

def main():
    OUT.mkdir(exist_ok=False)
    FIXTURES.mkdir(exist_ok=False)
    started = time.monotonic()
    stdout = io.StringIO()
    try:
        root = BASE.parents[1]
        receipt = json.loads((BASE/'implementation_candidate_v2_failure_freeze_v1.json').read_text())
        binding = json.loads((BASE/'consolidated_binding_v1/mother_and_training_design_binding_v1.json').read_text())
        old = json.loads((BASE/'implementation_candidate_v1_manifest.json').read_text())
        bound = [(root / x['path'], x['sha256']) for x in receipt['files'] + old['files']]
        bound += [(Path(x['parent_path']), x['sha256']) for x in binding['files']]
        for path, expected in bound:
            if sha(path) != expected:
                raise RuntimeError('bound source/previous artifact drift: ' + str(path))
        for path in (V2/'bcsp_cpu_entry_v2.py', V2/'test_cpu_integration_v2.py', Path(__file__)):
            ast.parse(path.read_text(encoding='utf8'))
        # Loading declarations only: neither historical __main__ is run.
        sys.path.insert(0, str(V2))
        current = import_file('bcsp_candidate_tests_v2', V2/'test_cpu_integration_v2.py')
        sys.modules['bcsp_adapter'] = current.a
        previous = import_file('bcsp_previous_tests_v3', current.entry.V1.parent/'test_bcsp_adapter.py')
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromModule(previous),
            unittest.defaultTestLoader.loadTestsFromTestCase(current.TensorTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(current.IntegrationTests),
        ])
        # tempfile module objects are shared by these two unchanged test modules.
        with patch('tempfile.TemporaryDirectory', RetainedFixtureDirectory):
            result = unittest.TextTestRunner(stream=stdout, verbosity=2, failfast=True).run(suite)
        unchanged = all(sha(path) == expected for path, expected in bound)
        ok = result.wasSuccessful() and not result.skipped and unchanged
        summary = {
            'status': 'PASS_CPU_TENSOR_AND_MINIMAL_CHAIN' if ok else 'FAILED_OR_INCOMPLETE_STOP',
            'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'skipped': [(str(t), why) for t, why in result.skipped],
            'python': sys.executable, 'python_version': sys.version,
            'torch': str(current.torch.__version__), 'numpy': current.np.__version__,
            'cuda_initialized': current.torch.cuda.is_initialized(),
            'seconds': time.monotonic()-started, 'bound_files_unchanged': unchanged,
            'fixture_policy': 'workspace-local retained; no cleanup deletion',
            'fixture_directories': len(list(FIXTURES.iterdir())),
            'real_model_calls': 0, 'real_data_access': 0, 'real_optimizer_updates': 0,
            'server_operations': 0, 'production_edits': 0, 'training_requests_created': 0,
            'limitations': [
                'No CUDA equivalence, GPU resource certification or actual model forward',
                'One real synthetic CPU DataLoader traversal; remaining traversals are counter-only batches',
                'Fake optimizer counter, no NN parameter training or real optimizer update',
                'Explicit isolated Dataset/epoch hook, not deployed full production runner',
                'No scheduler/loss/clip/checkpoint end-to-end model validation',
            ],
        }
        dump('result.json', summary)
        with (OUT/'stdout.txt').open('x', encoding='utf8') as f:
            f.write(stdout.getvalue())
        print(stdout.getvalue())
        print(json.dumps(summary, ensure_ascii=False))
        return 0 if ok else 1
    except BaseException:
        import traceback
        with (OUT/'failure.txt').open('x', encoding='utf8') as f:
            f.write(stdout.getvalue()); traceback.print_exc(file=f)
        raise

if __name__ == '__main__':
    raise SystemExit(main())
