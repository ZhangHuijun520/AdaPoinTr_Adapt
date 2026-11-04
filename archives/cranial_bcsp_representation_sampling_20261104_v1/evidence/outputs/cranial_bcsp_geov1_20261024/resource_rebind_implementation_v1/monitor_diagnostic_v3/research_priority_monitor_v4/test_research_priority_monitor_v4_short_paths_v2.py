"""One fixed artificial CPU batch; execute only the candidate resource class."""
import ast
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
BATCH = ROOT / 'cpu_verification_v2'
FIX = BATCH / 'fixtures'
LIMITS = dict(wall_seconds=86400, RSS_bytes=8589934592, device_MiB=22528,
              torch_peak_bytes=21474836480, output_bytes=2147483648,
              minimum_free_disk_bytes=4294967296)
NS = None

def require(condition, message):
    if not condition:
        raise ValueError(message)

class Contracts(unittest.TestCase):
    def budget(self, allocated=0, reserved=0, device=0, pids=None, pid_error=None):
        self.path = FIX / (self._testMethodName.split('_')[1] + getattr(self, 'fixture_suffix', '') + '.jsonl')
        self.path.open('x').close()
        obj = NS['TrainingBudget'].__new__(NS['TrainingBudget'])
        obj.path, obj.output, obj.start = self.path, FIX, time.monotonic()
        obj.records, obj.limits = 0, dict(LIMITS)
        obj.local = lambda: (1024, 2048)
        obj.torch = SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda: None,
            max_memory_allocated=lambda _: allocated, max_memory_reserved=lambda _: reserved))
        self.queries = []
        def smi(query, compute=False):
            self.queries.append((query, compute))
            if query == 'memory.used':
                return [str(device)]
            self.assertEqual((query, compute), ('pid', True))
            if pid_error:
                raise pid_error
            return [str(p) for p in (pids if pids is not None else [os.getpid()])]
        obj.helper = SimpleNamespace(smi=smi)
        return obj

    def event(self):
        rows = [json.loads(x) for x in self.path.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        e = rows[0]
        self.assertEqual(e['limits'], LIMITS)
        self.assertEqual(len(e['checks']), 3)
        self.assertEqual(e['PID_policy'], 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE')
        self.assertEqual(self.queries, [('memory.used', False), ('pid', True)])
        return e

    def test_01_original_failure_PID_mismatch_now_diagnostic(self):
        o = self.budget(12897085952, 14245953536, 14072, [2851712])
        with patch.object(os, 'getpid', return_value=1512):
            o.after_step(1)
        e = self.event()
        self.assertTrue(e['resource_guard_passed'])
        self.assertEqual(e['compute_PIDs'], [2851712])
        self.assertEqual(e['own_PID'], 1512)
        self.assertFalse(e['raw_PIDs_match_worker_number'])
        self.assertTrue(e['PID_warning'])

    def test_02_multiple_PIDs_no_ownership_claim(self):
        self.budget(pids=[os.getpid(), os.getpid()+1]).after_step(1)
        e = self.event()
        self.assertTrue(e['resource_guard_passed'] and e['PID_warning'])

    def test_03_empty_PID_list_no_false_ownership(self):
        self.budget(pids=[]).after_step(1)
        e = self.event()
        self.assertIsNone(e['raw_PIDs_match_worker_number'])
        self.assertTrue(e['PID_warning'])

    def test_04_PID_query_error_logged_no_retry(self):
        self.budget(pid_error=TimeoutError('artificial PID timeout')).after_step(1)
        e = self.event()
        self.assertIn('artificial PID timeout', e['PID_query_error'])
        self.assertIsNone(e['compute_PIDs'])
        self.assertTrue(e['resource_guard_passed'])

    def test_05_equal_memory_thresholds_pass(self):
        self.budget(LIMITS['torch_peak_bytes'], LIMITS['torch_peak_bytes'], LIMITS['device_MiB']).after_step(1)
        self.assertTrue(self.event()['resource_guard_passed'])

    def test_06_each_memory_over_limit_stops_after_fsync(self):
        for field, args in [('allocated_within_limit', dict(allocated=LIMITS['torch_peak_bytes']+1)),
                            ('reserved_within_limit', dict(reserved=LIMITS['torch_peak_bytes']+1)),
                            ('device_within_limit', dict(device=LIMITS['device_MiB']+1))]:
            self.fixture_suffix = '_' + field.split('_')[0]
            o = self.budget(**args)
            seen = []
            real = os.fsync
            def sync(fd):
                seen.append(self.event()['failed_checks'])
                real(fd)
            with patch.object(os, 'fsync', side_effect=sync):
                with self.assertRaisesRegex(ValueError, '^training GPU memory budget$'):
                    o.after_step(1)
            self.assertEqual(seen, [[field]])

    def test_07_PID_query_error_does_not_hide_memory_failure(self):
        o = self.budget(device=LIMITS['device_MiB']+1, pid_error=ValueError('artificial PID parse'))
        with self.assertRaisesRegex(ValueError, 'training GPU memory budget'):
            o.after_step(1)
        e = self.event()
        self.assertEqual(e['failed_checks'], ['device_within_limit'])
        self.assertIn('artificial PID parse', e['PID_query_error'])

    def test_08_journal_errors_remain_fatal(self):
        o = self.budget()
        with patch.object(os, 'fsync', side_effect=OSError('artificial fsync')):
            with self.assertRaisesRegex(OSError, 'artificial fsync'):
                o.after_step(1)
        class Broken:
            def open(self, *a, **kw):
                raise OSError('artificial write')
        o.path = Broken()
        with self.assertRaisesRegex(OSError, 'artificial write'):
            o.after_step(1)

    def test_09_record_cap_unchanged(self):
        o = self.budget();o.records = 3902
        with self.assertRaisesRegex(ValueError, 'fixed training resource record cap'):
            o.after_step(1)
        self.assertEqual(self.path.stat().st_size, 0)

    def test_10_local_resource_failure_still_prevents_GPU_query(self):
        o = self.budget()
        def fail():
            raise ValueError('artificial local RSS/output/disk/wall failure')
        o.local = fail
        with self.assertRaisesRegex(ValueError, 'artificial local'):
            o.after_step(1)
        self.assertEqual(self.queries, [])

def main():
    global NS
    BATCH.mkdir(exist_ok=False);FIX.mkdir()
    source = ast.parse((ROOT/'bcsp_training_entry_v4.py').read_text(encoding='utf-8'))
    node = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name=='TrainingBudget')
    NS = dict(os=os,json=json,time=time,Path=Path,shutil=None,require=require)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'candidate_TrainingBudget_only','exec'),NS)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contracts)
    assert suite.countTestCases()==10
    result = unittest.TextTestRunner(verbosity=2,failfast=True).run(suite)
    report = dict(status='PASS' if result.wasSuccessful() and result.testsRun==10 else 'FAILED_STOP_NO_RETRY',
                  testsRun=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                  real_resource_queries=0,CUDA_calls=0,model_forwards=0,optimizer_steps=0,server_operations=0)
    with (BATCH/'results_v1.json').open('x') as f:json.dump(report,f,indent=2)
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
