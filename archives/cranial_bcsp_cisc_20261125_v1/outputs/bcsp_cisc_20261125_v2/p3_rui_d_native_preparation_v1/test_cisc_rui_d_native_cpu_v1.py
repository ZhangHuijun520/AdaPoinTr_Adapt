"""Synthetic CPU contracts for CISC Native prediction preparation."""
import ast
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT.parent / "cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


entry = load("native_cpu_fixture", HERE / "cisc_rui_d_native_v1.py")
head = load("cisc_cpu_fixture", ROOT / "bcsp_cisc_head_v1.py")
oasg = load("oasg_cpu_fixture", ROOT.parent / "bcsp_oasg_20261124_v1/p1_implementation_v1/bcsp_oasg_head_v1.py")
request = json.loads((HERE / "CISC_RUI_D_native_execution_request_v1.json").read_bytes())


class Synthetic(torch.nn.Module):
    def __init__(self, arm, corrupt=False):
        super().__init__()
        original = oasg.ObservationAnchoredHead()
        self.base_model = torch.nn.Module()
        self.base_model.coarse_pred = original if arm == "R" else head.CiscObservationHead(original, arm, 0.02, 7)
        self.decode_head = torch.nn.Identity()
        self.arm, self.corrupt, self.calls = arm, corrupt, 0

    def forward(self, x):
        self.calls += 1
        anchors = x[:, :256].contiguous()
        memory = x.new_zeros(1, 256, 384)
        args = (x.new_zeros(1, 1024), memory, anchors)
        coarse, _ = self.base_model.coarse_pred(*args, *(() if self.arm == "R" else (x,)))
        relative = self.decode_head(x.new_zeros(1, 256, 32, 3))
        dense = (relative + coarse[:, :, None, :]).reshape(1, 8192, 3)
        return coarse, dense.flip(1) if self.corrupt else dense


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fold = json.loads((BASE / "fold_binding.json").read_bytes())
        points = list(map(json.loads, (BASE / "manifest_8192.jsonl").read_bytes().splitlines()))
        cls.rows = entry.select_inputs(request, fold, points)
        cls.ids = [r["case_id"] for r in cls.rows]
        cls.x = torch.linspace(-1, 1, 8192 * 3).reshape(1, 8192, 3)

    def test_full_forward_budget(self):
        budget = entry.ForwardBudget(self.ids)
        with self.assertRaises(ValueError):
            budget.claim("I", self.ids[0])
        for arm in entry.ARMS:
            for cid in self.ids:
                budget.claim(arm, cid)
        budget.finish(315)
        with self.assertRaises(ValueError):
            budget.claim("I", self.ids[-1])

    def test_fold_and_fixed_selection(self):
        self.assertEqual(len(self.rows), 105)
        self.assertEqual(len({r["source_id"] for r in self.rows}), 21)
        self.assertEqual(entry.mechanism_cases(self.rows), request["mechanism_cases"])
        self.assertEqual(len({"__".join(x.split("__")[:2]) for x in request["mechanism_cases"]}), 15)
        self.assertNotIn("label_root", request)
        self.assertNotIn("labels", request)

    def test_observer_real_cpu_heads(self):
        for arm in entry.ARMS:
            with self.subTest(arm=arm):
                model = Synthetic(arm).eval()
                rng = torch.get_rng_state().clone()
                state = {k: v.clone() for k, v in model.state_dict().items()}
                result = entry.observe_once(torch, np, model, self.x, arm)
                self.assertEqual(model.calls, 1)
                self.assertTrue(torch.equal(rng, torch.get_rng_state()))
                for k, v in model.state_dict().items():
                    self.assertTrue(torch.equal(v, state[k]))
                self.assertEqual(result["prediction"].shape, (8192, 3))
                self.assertEqual(np.bincount(result["parent_index"]).tolist(), [32] * 256)
                if arm == "R":
                    self.assertNotIn("p", result)
                else:
                    self.assertEqual(int(result["n"].sum()), 8192)
                    self.assertEqual(result["V"].shape, (6,))
                    self.assertEqual(result["c"].shape, (3,))

    def test_fc_order_and_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, "eval mode"):
            entry.observe_once(torch, np, Synthetic("R"), self.x, "R")
        with self.assertRaisesRegex(ValueError, "slot"):
            entry.observe_once(torch, np, Synthetic("I", True).eval(), self.x, "I")

    def test_authorization_request_and_runtime(self):
        auth = dict(schema="bcsp-development-authorization-v1", request_sha256="pending",
                    explicit_user_authorization=True, user_authorization_text="fixture only")
        runtime = dict(schema="bcsp-development-runtime-v1", request_sha256="pending", authorization_sha256="auth")
        entry.authorize(request, "pending", auth, "auth", runtime)
        with self.assertRaises(ValueError):
            entry.authorize(request, "pending", dict(auth, explicit_user_authorization=False), "auth", runtime)
        with self.assertRaises(ValueError):
            entry.authorize(request, "pending", auth, "auth", dict(runtime, request_sha256="wrong"))

    def test_frozen_three_training_receipts(self):
        receipts = {a: json.loads((HERE / f"{a}_D_formal_post_training_freeze_receipt_v1.json").read_bytes())
                    for a in entry.ARMS}
        entry.verify_training(request, receipts)
        with self.assertRaises(ValueError):
            entry.verify_training(request, dict(receipts, I=receipts["U"]))

    def test_file_boundary_accepts_only_registered_inputs_and_output(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            x = root / "point.npz"
            w = root / "ckpt-last.pth"
            out = root / "output"
            q = dict(project=str(root), checkpoints={"I": {"path": str(w)}})
            check = entry.data_boundary(q, [{"input": {"path": str(x)}, "case_id": "ex"}], out)
            for file in (x, w):
                check("open", (str(file), "r", 0))
            check("open", (str(out / "predictions/I_D__ex.npz"), "x", 64))
            for forbidden in ("ex_labels.npz", "implant.npy", "other.pth", "data/gt.json"):
                with self.assertRaises(ValueError):
                    check("open", (str(root / forbidden), "r", 0))

    def test_real_loader_uses_partial_only(self):
        legacy = ROOT.parent / "scq_pred_freeze_20261114_v2/downloads/installed/bcsp_scq_fourmodel_native_predict_v2.py"
        raw = legacy.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), request["legacy_helpers"]["sha256"])
        tree = ast.parse(raw)
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "load_partial")
        value = self.x[0].numpy().copy()
        class Bundle:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                pass
            def __getitem__(self, name):
                if name != "partial":
                    raise AssertionError(name)
                return value
        scope = {"exact": lambda r: r["path"], "require": entry.need}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(legacy), "exec"), scope)
        with patch.object(np, "load", return_value=Bundle()) as read:
            np.testing.assert_array_equal(scope["load_partial"](np, self.rows[0]), value)
        self.assertEqual(read.call_args.kwargs, {"allow_pickle": False})


if __name__ == "__main__":
    torch.set_num_threads(2)
    unittest.main(verbosity=2)
