"""Artificial comparison. The Linux freeze, not this host, supplies the exact seed0 hash."""

import hashlib
import json
import runpy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import CodeType
from unittest.mock import patch

import torch


HERE = Path(__file__).resolve().parent
P4 = HERE.parent
B0 = runpy.run_path(str(P4 / "bcsp_fcsp_p4_train_B0_D_v1.py"))
B1 = runpy.run_path(str(P4 / "bcsp_fcsp_p4_train_B1_D_v1.py"))
for runtime in (B0, B1):
    runtime["load_numeric"]()
torch.set_num_threads(2)

source = P4.parent / "fcsp_isolated_implementation_20261120_v1/bcsp_fcsp_head_v1.py"
raw = source.read_bytes()
HEAD = B1["load_head"](dict(path=str(source), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))


def fixture():
    q = torch.arange(768, dtype=torch.float32).reshape(256, 3) / 1024
    p0 = q[:, None, :].expand(256, 32, 3).clone() + .125
    return {"case": (dict(Q=q, P0=p0), None)}


def bytecode(fn):
    def key(c):
        return c.co_code, tuple(key(x) if isinstance(x, CodeType) else x for x in c.co_consts), c.co_names
    return key(fn.__code__)


class Pair(unittest.TestCase):
    def test_same_runtime_components_and_distinct_condition(self):
        names = ("learning_rate", "load_row", "load_loss", "bind_training", "validate_order",
                 "train_step", "build_training", "make_monitor")
        for name in names:
            self.assertEqual(bytecode(B0[name]), bytecode(B1[name]), name)
        g = torch.arange(2560, dtype=torch.float32).reshape(1, 256, 10)
        self.assertTrue(torch.equal(HEAD["geometry_condition"](g, B1["ARM"]), g))
        self.assertTrue(torch.equal(HEAD["geometry_condition"](g, B0["ARM"]), g.mean(1, keepdim=True).expand_as(g)))
        self.assertNotEqual(B0["ARM"], B1["ARM"])

    def test_same_host_initializer_and_scale(self):
        a, sa = B0["build_training"](HEAD, fixture(), "cpu")
        b, sb = B1["build_training"](HEAD, fixture(), "cpu")
        self.assertEqual(sa, sb)
        self.assertEqual(B0["state_sha"](a), B1["state_sha"](b))
        self.assertTrue(all(torch.count_nonzero(x) == 0 for x in b.net[-1].parameters()))

    def test_pair_mismatch_blocks_before_update(self):
        ds = fixture()
        model, scale = B0["build_training"](HEAD, ds, "cpu")
        opt = torch.optim.AdamW(model.parameters(), lr=.001, betas=(.9,.999), eps=1e-8,
                                weight_decay=.0001, foreach=False, fused=False)
        expected = dict(seed=0, state_sha256=B0["state_sha"](model), b_train_fp64=scale,
                        b_train_float32_bytes=model.b_train.numpy().tobytes().hex(),
                        trainable_parameters=sum(w.numel() for w in model.parameters()),
                        optimizer=json.loads(json.dumps(opt.defaults)))
        epochs = [dict(epoch=0, batches=[["case"]], dropped=[])]
        with TemporaryDirectory(dir=HERE) as folder:
            target = Path(folder)
            globals_ = B1["train"].__globals__
            with patch.dict(globals_, train_step=lambda *_: self.fail("update entered before pairing")):
                for key, wrong in (("state_sha256", "0"*64), ("b_train_fp64", scale+1),
                                   ("b_train_float32_bytes", "00000000"), ("optimizer", {})):
                    with self.subTest(key=key), self.assertRaisesRegex(ValueError, "mismatch"):
                        B1["train"](HEAD, None, ds, epochs, "cpu", target, "fixture",
                                    lambda _: None, {**expected, key:wrong})
                    self.assertFalse(list(target.iterdir()))

            def reached(*_):
                raise RuntimeError("reached first update")

            with patch.dict(globals_, train_step=reached), self.assertRaisesRegex(RuntimeError, "first update"):
                B1["train"](HEAD, None, ds, epochs, "cpu", target, "fixture", lambda _: None, expected)
            self.assertEqual(json.loads((target/"initialization.json").read_bytes()), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
