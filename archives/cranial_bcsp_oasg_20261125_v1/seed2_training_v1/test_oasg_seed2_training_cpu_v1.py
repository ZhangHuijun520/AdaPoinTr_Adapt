"""Check new seed bindings with the frozen evidence and artificial RNG devices."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import oasg_train_seed2_b_d_v1 as worker


HERE = Path(__file__).resolve().parent


class Seed2Contract(unittest.TestCase):
    def setUp(self):
        receipt = HERE / "seed2_cpu_initialization_receipt_v1.json"
        self.receipt = json.loads(receipt.read_bytes())
        self.q = json.loads((HERE.parent / "p3_a_d_v1/OASG_A_D_training_execution_request_v1.json").read_bytes())
        self.q.update(schema="bcsp-oasg-seed2-b-d-train-v1", run=worker.RUN,
                      shared_initial_state_sha256=worker.SHARED)
        entry = HERE / "bcsp_oasg_entry_seed2_v1.py"
        self.q["implementation"]["oasg_entry"]["sha256"] = hashlib.sha256(entry.read_bytes()).hexdigest()

    def test_historical_cuda_and_new_cpu_initialization_are_separate(self):
        p2 = json.loads((HERE.parent / "P2_formal_post_CUDA_freeze_receipt_v1.json").read_bytes())
        worker.check_admission(p2, self.q)
        self.assertEqual(worker.check_cpu_evidence(self.receipt, self.q)["run_identity"], worker.RUN)
        with self.assertRaisesRegex(ValueError, "CPU initialization"):
            worker.check_cpu_evidence(self.receipt, {**self.q, "initialization": {"sha256": "wrong"}})
        with self.assertRaisesRegex(ValueError, "same-device"):
            worker.check_admission({**p2, "identity": {}}, self.q)

    def test_authorization_rejects_seed_one_state(self):
        r, a = "a" * 64, "b" * 64
        auth = dict(schema="bcsp-oasg-seed2-b-d-authorization-v1", request_sha256=r,
                    explicit_user_authorization=True, user_authorization_text="artificial")
        runtime = dict(schema="bcsp-oasg-seed2-b-d-runtime-v1", request_sha256=r, authorization_sha256=a)
        worker.authorize(self.q, r, auth, a, runtime)
        for q in ({**self.q, "run": {**worker.RUN, "seed": 2026112101}},
                  {**self.q, "shared_initial_state_sha256": worker.P2_SHARED}):
            with self.assertRaisesRegex(ValueError, "science"):
                worker.authorize(q, r, auth, a, runtime)

    def test_actual_first_step_callback_and_rng_exclusive_write(self):
        expected = self.receipt["models"][0]["training_start_rng"]
        t = SimpleNamespace(cuda=SimpleNamespace(initial_seed=lambda: worker.RUN["seed"],
                            max_memory_reserved=lambda i: 0, max_memory_allocated=lambda i: 0))
        e = SimpleNamespace(rng_fingerprints=lambda np, device: {**expected, "torch_cuda": "a" * 64})
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "training_start_rng.json"
            events = []
            guard = worker.TrainingResources(Path(tmp), t, SimpleNamespace(assert_numeric=lambda t: None),
                                             dict, events.append, 100,
                                             lambda: worker.record_rng(p, e, None, t, expected))
            guard.before_step(0)
            guard.before_step(1)
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(p.read_bytes())["rng"]["torch_cuda"], "a" * 64)
            with self.assertRaises(FileExistsError):
                worker.record_rng(p, e, None, t, expected)
            t.cuda.initial_seed = lambda: 2026112101
            with self.assertRaisesRegex(ValueError, "CUDA seed"):
                worker.record_rng(p, e, None, t, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
