"""Use real frozen Fold C metadata and artificial model/lifecycle boundaries."""
import ast
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import oasg_train_b_c_v1 as worker


HERE = Path(__file__).resolve().parent
TOP = HERE.parents[2]
EXP = HERE.parent
ORDER = TOP / "outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/shared_order_foldC_seed0_v1.json"
PARENT = TOP / "outputs/scq_prime_entry_20261121_v1/bcsp_scq_prime_runtime_v1.py"


def read(p):
    return json.loads(p.read_bytes())


def functions(path, names, scope):
    tree = ast.parse(path.read_bytes(), str(path))
    subset = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=subset, type_ignores=[]), str(path), "exec"), scope)
    return scope


class FoldCPairContract(unittest.TestCase):
    def setUp(self):
        self.q = read(EXP / "p3_b_d_v1/OASG_B_D_training_execution_request_v1.json")
        self.q.update(schema="bcsp-oasg-p6-b-c-train-v1", run=worker.RUN, order={"sha256": worker.ORDER_SHA})
        self.order = read(ORDER)

    def test_fold_c_frozen_training_metadata_and_order(self):
        refs = read(EXP / "P3_B_D_training_request_preparation_v1.json")["local_reference_bindings"]
        def raw(key):
            f = refs[key]
            b = (TOP / f["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(), f["sha256"])
            return b
        self.assertEqual(hashlib.sha256(ORDER.read_bytes()).hexdigest(), worker.ORDER_SHA)
        rows, sources = worker.select_training(json.loads(raw("fold")),
                                               list(map(json.loads, raw("point_manifest").splitlines())),
                                               self.order)
        self.assertEqual((len(rows), len(sources)), (315, 63))
        self.assertEqual([row["case_id"] for row in rows], self.order["case_ids"])

    def test_one_way_authorization_rejects_old_fold(self):
        r, a = "1" * 64, "2" * 64
        auth = dict(schema="bcsp-oasg-p6-b-c-authorization-v1", request_sha256=r,
                    explicit_user_authorization=True, user_authorization_text="artificial")
        runtime = dict(schema="bcsp-oasg-p6-b-c-runtime-v1", request_sha256=r, authorization_sha256=a)
        worker.authorize(self.q, r, auth, a, runtime)
        worker.check_admission(read(EXP / "P2_formal_post_CUDA_freeze_receipt_v1.json"), self.q)
        with self.assertRaisesRegex(ValueError, "science"):
            worker.authorize({**self.q, "run": {**worker.RUN, "fold": "D"}}, r, auth, a, runtime)

    def test_shared_entry_only_changes_fold_identity(self):
        old = (EXP / "p1_implementation_v1/bcsp_oasg_entry_v1.py").read_bytes()
        expected = old.replace(b"Fold D B/A", b"Fold C B/A").replace(b'fold == "D"', b'fold == "C"')
        self.assertEqual((HERE / "bcsp_oasg_entry_foldc_v1.py").read_bytes(), expected)

    def test_actual_fold_c_bridge_accepts_both_arms_and_dispatches_b(self):
        checked = []
        scope = {}
        class StopAtMetadata(Exception):
            pass
        def ordered(plan, ids):
            checked.append((plan, ids))
            raise StopAtMetadata
        ns = functions(PARENT, {"train_lifecycle"}, {"require": worker.need, "validate_order": ordered})
        names = {"identity", "_source", "_same_statement", "_compile", "bind_training_lifecycle"}
        entry = functions(HERE / "bcsp_oasg_entry_foldc_v1.py", names,
                          dict(ast=ast, Path=Path, hashlib=hashlib, require=worker.need, TRAIN_SEED=2026112101,
                               RUNTIME_SHA256=self.q["implementation"]["training_runtime"]["sha256"]))
        for arm in ("B", "A"):
            self.assertEqual(entry["identity"](arm, "C", 2026112101)["variant"], arm)
        with self.assertRaisesRegex(ValueError, "Fold C"):
            entry["identity"]("A", "D", 2026112101)
        parent = SimpleNamespace(train_lifecycle=ns["train_lifecycle"],
                                 BCSPDataset=lambda root, rows, sources, n: self.assertEqual(n, 8192))
        bridge = entry["bind_training_lifecycle"](parent)
        with self.assertRaises(StopAtMetadata):
            bridge(None, None, [{"case_id": "fixture_A"}], self.order, None, device="cpu", numeric_check=None,
                   resources=None, knn_enable=None, state_fingerprint=None, run_identity=dict(variant="A",fold="C",seed=2026112101))
        @contextmanager
        def observe(model, run, resources, emit):
            self.assertEqual(run, worker.RUN)
            yield resources
        wrapper = SimpleNamespace(bind_training_lifecycle=entry["bind_training_lifecycle"], observe_training=observe)
        evidence = dict(artificial_fixture=False, run_identity=worker.RUN, initializer_sha256=None,
                        historical_B_initial_state_SHA256=worker.HISTORICAL_B,
                        shared_initial_state_SHA256=self.q["shared_initial_state_sha256"])
        helper = SimpleNamespace(assert_numeric=None, state_sha=None)
        with self.assertRaises(StopAtMetadata):
            worker.dispatch(self.q, object(), evidence, wrapper, parent, [{"case_id": "fixture_B"}],
                            [], self.order, None, helper, None, None, "cuda:0")
        self.assertEqual(checked, [(self.order, ["fixture_A"]), (self.order, ["fixture_B"])])
        self.assertNotIn("claim_output", ns)


if __name__ == "__main__":
    unittest.main(verbosity=2)
