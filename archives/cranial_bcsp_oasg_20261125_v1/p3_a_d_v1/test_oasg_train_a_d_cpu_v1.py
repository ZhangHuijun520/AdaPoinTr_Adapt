"""CPU contracts for the Fold D A-arm adapter. Uses frozen metadata and artificial stubs."""

import ast
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import oasg_train_a_d_v1 as worker


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


def read(path):
    return json.loads(path.read_bytes())


def nodes(path, names):
    tree = ast.parse(path.read_bytes(), str(path))
    return [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names
    ]


class TrainingContract(unittest.TestCase):
    def setUp(self):
        baseline_path = HERE.parent / "p3_b_d_v1/B_D_formal_post_training_freeze_receipt_v1.json"
        self.assertEqual(hashlib.sha256(baseline_path.read_bytes()).hexdigest(), worker.BASELINE_RECEIPT_SHA)
        self.baseline = read(baseline_path)
        self.p2 = read(HERE.parent / "P2_formal_post_CUDA_freeze_receipt_v1.json")
        p2_request = read(HERE.parent / "p2_final_request_v1/OASG_P2_cuda_execution_request_v1.json")
        self.q = read(HERE.parent / "p3_b_d_v1/OASG_B_D_training_execution_request_v1.json")
        self.q.update(
            schema="bcsp-oasg-p3-a-d-train-v1",
            run=worker.RUN,
            paired_B_request_sha256=self.baseline["request_sha256"],
            paired_B_checkpoint=next(r for r in self.baseline["artifacts"] if r["path"].endswith("/ckpt-last.pth")),
            baseline_receipt=dict(sha256=worker.BASELINE_RECEIPT_SHA),
            initialization=p2_request["initialization"],
        )

    def test_authorization_is_bound_to_a_and_paired_contract(self):
        request_sha, auth_sha = "1" * 64, "2" * 64
        auth = dict(schema="bcsp-oasg-p3-a-d-authorization-v1", request_sha256=request_sha,
                    explicit_user_authorization=True, user_authorization_text="artificial")
        cfg = dict(schema="bcsp-oasg-p3-a-d-runtime-v1", request_sha256=request_sha,
                   authorization_sha256=auth_sha)
        worker.authorize(self.q, request_sha, auth, auth_sha, cfg)
        for key, value in (("run", worker.BASELINE_RUN), ("execution_authorized", True),
                           ("baseline_receipt", {"sha256": "0" * 64}),
                           ("initialization", {**self.q["initialization"], "seed": 0}),
                           ("counts", {**self.q["counts"], "updates": 3899})):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "frozen"):
                worker.authorize({**self.q, key: value}, request_sha, auth, auth_sha, cfg)
        with self.assertRaisesRegex(ValueError, "runtime"):
            worker.authorize(self.q, request_sha, auth, auth_sha, {**cfg, "authorization_sha256": "3" * 64})

    def test_actual_baseline_receipt_and_p2_match(self):
        worker.check_admission(self.p2, self.q)
        worker.check_baseline(self.baseline, self.q)
        for section, key, value in (
            ("fold_order", "all_actual_batches_verified", 3899),
            ("completion", "checkpoint_sha256", "0" * 64),
            ("model_construction", "shared_initial_state_SHA256", "0" * 64),
            ("identity", "gpu_uuid", "different"),
        ):
            modified = deepcopy(self.baseline)
            modified[section][key] = value
            with self.subTest(section=section), self.assertRaises(ValueError):
                worker.check_baseline(modified, self.q)

    def test_candidate_constructor_checks_exact_bytes_before_entry(self):
        path = HERE.parent / "p1_implementation_v1/artificial_cpu_v1/OASG_head_init_seed2026112402_v1.bin"
        init = self.q["initialization"]
        calls = []

        def exact(record):
            raw = path.read_bytes()
            worker.need(len(raw) == record["bytes"]
                        and hashlib.sha256(raw).hexdigest() == record["sha256"], "exact")
            calls.append("exact")

        def construct(run, builder, record, **bindings):
            self.assertEqual(run, worker.RUN)
            self.assertEqual(record, init)
            self.assertEqual(builder(), "untrained mother")
            self.assertEqual(set(bindings), {"np", "prime", "seeded", "lqi", "scq"})
            calls.append("construct")
            return "candidate"

        args = (SimpleNamespace(exact=exact), SimpleNamespace(construct=construct), lambda: "untrained mother")
        kwargs = dict(np=None, prime=None, seeded=None, lqi=None, scq=None)
        self.assertEqual(worker.make_candidate(self.q, *args, **kwargs), "candidate")
        with self.assertRaisesRegex(ValueError, "exact"):
            worker.make_candidate({**self.q, "initialization": {**init, "sha256": "0" * 64}}, *args, **kwargs)
        self.assertEqual(calls, ["exact", "construct"])

    def test_real_lifecycle_bridge_dispatch_until_first_metadata_check(self):
        entry = HERE.parent / "p1_implementation_v1/bcsp_oasg_entry_v1.py"
        runtime = PROJECT / "outputs/scq_prime_entry_20261121_v1/bcsp_scq_prime_runtime_v1.py"
        observed = []

        class StopAtMetadata(Exception):
            pass

        def validate_order(plan, ids):
            observed.append((plan, ids))
            raise StopAtMetadata

        namespace = {"require": worker.need, "validate_order": validate_order}
        exec(compile(ast.Module(body=nodes(runtime, {"train_lifecycle"}), type_ignores=[]), str(runtime),
                     "exec"), namespace)
        scope = {"Path": Path, "ast": ast, "hashlib": hashlib, "require": worker.need,
                 "TRAIN_SEED": worker.RUN["seed"], "RUNTIME_SHA256": self.q["implementation"]["training_runtime"]["sha256"]}
        helpers = {"identity", "_source", "_same_statement", "_compile", "bind_training_lifecycle"}
        exec(compile(ast.Module(body=nodes(entry, helpers), type_ignores=[]), str(entry), "exec"), scope)

        @contextmanager
        def observe(model, run, resources, emit):
            self.assertEqual(run, worker.RUN)
            yield resources

        bridge = SimpleNamespace(bind_training_lifecycle=scope["bind_training_lifecycle"], observe_training=observe)
        parent = SimpleNamespace(train_lifecycle=namespace["train_lifecycle"],
                                 BCSPDataset=lambda root, rows, sources, n: self.assertEqual(n, 8192))
        evidence = dict(artificial_fixture=False, run_identity=worker.RUN, initializer_sha256=worker.HEAD_SHA,
                        shared_tensors=410, total_parameters=39907012,
                        historical_B_initial_state_SHA256=worker.HISTORICAL_B,
                        shared_initial_state_SHA256=self.q["shared_initial_state_sha256"])
        helper = SimpleNamespace(assert_numeric=None, state_sha=None)
        args = (bridge, parent, [{"case_id": "artificial"}], [], {}, None, helper, None, None, "cuda:0")
        with self.assertRaisesRegex(ValueError, "native A"):
            worker.dispatch(self.q, object(), {**evidence, "initializer_sha256": None}, *args)
        with self.assertRaises(StopAtMetadata):
            worker.dispatch(self.q, object(), evidence, *args)
        self.assertEqual(observed, [({}, ["artificial"])])
        self.assertNotIn("claim_output", namespace)


if __name__ == "__main__":
    unittest.main(verbosity=2)
