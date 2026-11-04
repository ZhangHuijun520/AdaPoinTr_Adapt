"""Artificial CPU-only monitor regression; no torch import, server or real data."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parent
BATCH = ROOT / 'cpu_regression_v1'
FIX = BATCH / 'fixtures'
ENTRY = None
LIMITS = {'wall_seconds': 86400, 'RSS_bytes': 8 * 1024**3, 'device_MiB': 22528,
          'torch_peak_bytes': 20 * 1024**3, 'output_bytes': 2 * 1024**3,
          'minimum_free_disk_bytes': 4 * 1024**3}


class MonitorContracts(unittest.TestCase):
    def budget(self, *, allocated=0, reserved=0, device=0, pids=None):
        self.journal = FIX / (self._testMethodName + '.jsonl')
        self.journal.open('x', encoding='utf-8').close()
        obj = ENTRY.TrainingBudget.__new__(ENTRY.TrainingBudget)
        obj.path, obj.output = self.journal, FIX
        obj.start, obj.records, obj.limits = time.monotonic(), 0, dict(LIMITS)
        obj.local = lambda: (1024, 2048)
        self.calls = []
        def sync():
            self.calls.append('synchronize')
        def read_peak(value):
            def result(index):
                self.assertEqual(index, 0)
                return value
            return result
        obj.torch = SimpleNamespace(cuda=SimpleNamespace(
            synchronize=sync,
            max_memory_allocated=read_peak(allocated),
            max_memory_reserved=read_peak(reserved)))
        def smi(query, compute=False):
            self.calls.append((query, compute))
            if query == 'memory.used' and compute is False:
                return [str(device)]
            self.assertEqual((query, compute), ('pid', True))
            return [str(pid) for pid in (pids if pids is not None else [os.getpid()])]
        obj.helper = SimpleNamespace(smi=smi)
        return obj

    def event(self):
        values = [json.loads(x) for x in self.journal.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(values), 1)
        value = values[0]
        self.assertEqual(value['limits'], LIMITS)
        self.assertEqual(value['committed_step'], 1)
        self.assertEqual(value['own_PID'], os.getpid())
        self.assertEqual((value['RSS'], value['output_bytes']), (1024, 2048))
        self.assertEqual(self.calls, ['synchronize', ('memory.used', False), ('pid', True)])
        return value

    def stopped(self, budget, failed):
        with self.assertRaisesRegex(ValueError, '^training GPU/other-process budget$'):
            budget.after_step(1)
        value = self.event()
        self.assertEqual(value['failed_checks'], failed)
        self.assertFalse(value['resource_guard_passed'])
        self.assertEqual(budget.records, 1)
        return value

    def test_R01_equal_thresholds_pass_and_log(self):
        obj = self.budget(allocated=LIMITS['torch_peak_bytes'],
                          reserved=LIMITS['torch_peak_bytes'], device=LIMITS['device_MiB'])
        obj.after_step(1)
        value = self.event()
        self.assertTrue(value['resource_guard_passed'])
        self.assertTrue(all(value['checks'].values()))
        self.assertEqual(value['failed_checks'], [])

    def test_R02_allocated_over_stops_after_persist(self):
        value = self.stopped(self.budget(allocated=LIMITS['torch_peak_bytes'] + 1),
                             ['allocated_within_limit'])
        self.assertEqual(value['peak_allocated'], LIMITS['torch_peak_bytes'] + 1)

    def test_R03_reserved_over_stops_after_persist(self):
        value = self.stopped(self.budget(reserved=LIMITS['torch_peak_bytes'] + 1),
                             ['reserved_within_limit'])
        self.assertEqual(value['peak_reserved'], LIMITS['torch_peak_bytes'] + 1)

    def test_R04_device_over_stops_after_persist(self):
        value = self.stopped(self.budget(device=LIMITS['device_MiB'] + 1), ['device_within_limit'])
        self.assertEqual(value['device_MiB'], LIMITS['device_MiB'] + 1)

    def test_R05_foreign_PID_stops_and_records_full_list(self):
        pids = [os.getpid(), os.getpid() + 1]
        value = self.stopped(self.budget(pids=pids), ['compute_PIDs_owned'])
        self.assertEqual(value['compute_PIDs'], pids)

    def test_R06_multiple_failures_all_reported(self):
        keys = ['allocated_within_limit', 'reserved_within_limit',
                'device_within_limit', 'compute_PIDs_owned']
        value = self.stopped(self.budget(allocated=LIMITS['torch_peak_bytes'] + 3,
                                         reserved=LIMITS['torch_peak_bytes'] + 5,
                                         device=LIMITS['device_MiB'] + 7,
                                         pids=[os.getpid() + 2]), keys)
        self.assertEqual(list(value['checks']), keys)
        self.assertFalse(any(value['checks'].values()))

    def test_R07_fsync_observes_record_before_assertion(self):
        obj = self.budget(allocated=LIMITS['torch_peak_bytes'] + 1)
        calls = []
        real_fsync = os.fsync
        def observe(fd):
            value = self.event()
            self.assertFalse(value['resource_guard_passed'])
            calls.append('durable_record_before_guard')
            real_fsync(fd)
        with patch.object(ENTRY.os, 'fsync', side_effect=observe):
            with self.assertRaisesRegex(ValueError, 'training GPU/other-process budget'):
                obj.after_step(1)
        self.assertEqual(calls, ['durable_record_before_guard'])

    def test_R08_journal_write_failure_stops(self):
        obj = self.budget()
        class BrokenPath:
            def open(self, *args, **kwargs):
                raise OSError('artificial journal failure')
        obj.path = BrokenPath()
        with self.assertRaisesRegex(OSError, 'artificial journal failure'):
            obj.after_step(1)
        self.assertEqual(self.journal.stat().st_size, 0)

    def test_R09_fsync_failure_stops_even_with_valid_resources(self):
        obj = self.budget()
        with patch.object(ENTRY.os, 'fsync', side_effect=OSError('artificial fsync failure')):
            with self.assertRaisesRegex(OSError, 'artificial fsync failure'):
                obj.after_step(1)
        self.assertTrue(self.event()['resource_guard_passed'])

    def test_R10_record_cap_unchanged_no_extra_write(self):
        obj = self.budget()
        obj.records = 3902
        with self.assertRaisesRegex(ValueError, '^fixed training resource record cap$'):
            obj.after_step(1)
        self.assertEqual(self.journal.stat().st_size, 0)
        self.assertEqual(obj.records, 3903)


def main():
    global ENTRY
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    BATCH.mkdir(exist_ok=False)
    FIX.mkdir()
    spec = importlib.util.spec_from_file_location('bcsp_monitor_v3_artificial_CPU',
                                                 ROOT / 'bcsp_training_entry_v3.py')
    ENTRY = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ENTRY)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MonitorContracts)
    assert suite.countTestCases() == 10
    started = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(suite)
    report = {'status': 'PASS_10_ARTIFICIAL_CPU_ONLY' if result.wasSuccessful() and result.testsRun == 10
              else 'FAILED_STOP_NO_AUTOMATIC_RETRY',
              'testsRun': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'elapsed_seconds': time.monotonic() - started, 'server_operations': 0,
              'CUDA_calls': 0, 'model_forwards': 0, 'optimizer_steps': 0,
              'limits': LIMITS, 'real_resource_queries': 0, 'production_lifecycle_executed': False}
    with (BATCH / 'results_v1.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return 0 if report['status'] == 'PASS_10_ARTIFICIAL_CPU_ONLY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
