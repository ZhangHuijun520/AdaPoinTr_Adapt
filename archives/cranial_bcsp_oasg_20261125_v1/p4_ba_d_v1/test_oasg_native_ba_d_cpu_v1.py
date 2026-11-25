"""Exercise the fixed Native call schedule and output contracts with artificial tensors."""
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
import oasg_native_ba_d_v1 as worker


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


class Tensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class HookPoint:
    def __init__(self):
        self.hooks = []

    def register_forward_hook(self, callback):
        self.hooks.append(callback)
        return SimpleNamespace(remove=lambda: self.hooks.remove(callback))

    def emit(self, inputs, output):
        for cb in self.hooks:
            cb(self, inputs, output)


class Model:
    training = False

    def __init__(self, arm):
        self.arm = arm
        self.calls = 0
        self.decode_head = HookPoint()
        self.base_model = SimpleNamespace(coarse_pred=HookPoint())

    def modules(self):
        yield self

    def __call__(self, x):
        self.calls += 1
        anchors = np.arange(768, dtype=np.float32).reshape(1, 256, 3) / 64
        delta = np.full_like(anchors, -0.5)
        q = anchors + delta if self.arm == "A" else anchors
        if self.arm == "A":
            self.base_model.coarse_pred.emit((None, None, Tensor(anchors)), (Tensor(q), Tensor(delta)))
        relative = np.broadcast_to(np.arange(32, dtype=np.float32)[None, None, :, None], (1, 256, 32, 3))
        self.decode_head.emit((), Tensor(relative))
        return Tensor(q), Tensor((q[:, :, None, :] + relative).reshape(1, 8192, 3))


class NativeContract(unittest.TestCase):
    def test_exact_210_calls_and_observational_hooks(self):
        ids = [str(i) for i in range(105)]
        budget = worker.ForwardBudget(ids)
        with self.assertRaisesRegex(ValueError, "order"):
            budget.claim("A", "0")
        for arm in worker.ARMS:
            model = Model(arm)
            for cid in ids:
                number = budget.claim(arm, cid)
                result = worker.observe_once(SimpleNamespace(inference_mode=nullcontext), np, model, None, arm)
                self.assertEqual(number, model.calls + (105 if arm == "A" else 0))
                self.assertTrue(np.array_equal(result["parent_index"], np.repeat(np.arange(256), 32)))
                self.assertTrue(np.array_equal(result["prediction"][::32], result["coarse"]))
                self.assertFalse(model.decode_head.hooks)
                self.assertFalse(model.base_model.coarse_pred.hooks)
                if arm == "A":
                    self.assertTrue(np.array_equal(result["coarse"], result["S"] + result["delta"]))
                    self.assertTrue(np.array_equal(result["token_index"], np.arange(256)))
                else:
                    self.assertNotIn("S", result)
            self.assertEqual(model.calls, 105)
        budget.finish(210)
        with self.assertRaisesRegex(ValueError, "budget"):
            budget.claim("B", "0")

    def test_reject_changed_parent_or_anchor(self):
        s = np.zeros((1, 256, 3), dtype=np.float32)
        delta = np.ones_like(s)
        q = s + delta
        relative = np.zeros((1, 256, 32, 3), dtype=np.float32)
        p = (q[:, :, None, :] + relative).reshape(1, 8192, 3)
        bad = p.copy()
        bad[0, 3] += 1
        with self.assertRaisesRegex(ValueError, "parent-major"):
            worker.payload(np, "B", q, bad, relative)
        with self.assertRaisesRegex(ValueError, "consumed"):
            worker.payload(np, "A", q, p, relative, (s, q, -delta))

    def test_native_authorization_and_runtime_binding(self):
        request, authorization = "a" * 64, "b" * 64
        q = dict(schema=worker.SCHEMA, status=worker.STATUS, execution_authorized=False,
                 science=dict(fold="D", seed=worker.SEED, arms=["B", "A"], cases=105, sources=21,
                              forward=210, n_input=8192, n_output=8192, batch=1), no_calls=worker.CALLS)
        a = dict(schema="bcsp-development-authorization-v1", explicit_user_authorization=True,
                 request_sha256=request, user_authorization_text="artificial")
        runtime = dict(schema="bcsp-development-runtime-v1", request_sha256=request,
                       authorization_sha256=authorization)
        worker.authorize(q, request, a, authorization, runtime)
        with self.assertRaisesRegex(ValueError, "scope"):
            worker.authorize({**q, "science": {**q["science"], "forward": 211}}, request, a, authorization, runtime)
        with self.assertRaisesRegex(ValueError, "runtime"):
            worker.authorize(q, request, a, "c" * 64, runtime)

    def test_frozen_training_pair(self):
        paths = {
            "B": HERE.parent / "p3_b_d_v1/B_D_formal_post_training_freeze_receipt_v1.json",
            "A": HERE.parent / "p3_a_d_v1/A_D_formal_post_training_pair_freeze_receipt_v1.json",
        }
        reads = {a: json.loads(p.read_bytes()) for a, p in paths.items()}
        q = dict(identity=reads["B"]["identity"],
                 shared_initial_state_sha256=reads["B"]["model_construction"]["shared_initial_state_SHA256"],
                 training_receipts={a: dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for a,p in paths.items()},
                 checkpoints={a: next(r for r in receipt["artifacts"] if r["path"].endswith("/ckpt-last.pth"))
                              for a, receipt in reads.items()})
        worker.verify_training(q, reads)
        changed = deepcopy(reads)
        changed["A"]["paired_B_D"]["all_actual_batches_pairwise_verified"] = 3899
        with self.assertRaisesRegex(ValueError, "paired training"):
            worker.verify_training(q, changed)

    def test_ordered_development_metadata_and_read_boundary(self):
        draft = json.loads((HERE.parent / "P3_B_D_training_request_preparation_v1.json").read_bytes())
        metadata = {}
        for name in ("fold", "point_manifest"):
            ref = draft["local_reference_bindings"][name]
            raw = (PROJECT / ref["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref["sha256"])
            metadata[name] = raw
        f = json.loads(metadata["fold"])
        ids = f["folds"]["D"]["dev_case_ids"]
        base = (HERE / "artificial_project").resolve()
        root = base / "data/dev"
        out = base / "logs/native"
        q = dict(project=str(base), development_root=str(root), development_sizes={cid: 123 for cid in ids},
                 checkpoints=dict(B=dict(path=str(base / "B.pth")), A=dict(path=str(base / "A.pth"))))
        rows = worker.select_inputs(q, f, list(map(json.loads, metadata["point_manifest"].splitlines())))
        self.assertEqual([r["case_id"] for r in rows], ids)
        policy = worker.data_boundary(q, rows, out)
        policy("open", (rows[0]["input"]["path"], "r", os.O_RDONLY))
        policy("open", (str(out / ("predictions/A_D__" + ids[0] + ".npz")), "x", os.O_CREAT | os.O_WRONLY))
        for p, flags in ((base / "data/train/payload.npz", os.O_RDONLY), (base / "X.pth", os.O_RDONLY),
                         (Path(rows[0]["input"]["path"]), os.O_WRONLY), (out / "../bad", os.O_WRONLY)):
            with self.assertRaisesRegex(ValueError, "out-of-scope"):
                policy("open", (str(p), "r", flags))


if __name__ == "__main__":
    unittest.main(verbosity=2)
