import ast
from contextlib import nullcontext
import copy
from pathlib import Path
import types
import unittest

import numpy as np

import rbss_prefix16_v1 as probe


def make_scope():
    h = "a" * 64
    return dict(schema="bcsp-rbss-p0b-prefix16-v1", status="PENDING_SERVER_BINDING", execution_authorized=False,
                plan_sha256=probe.PLAN_SHA, pilot_result_sha256=probe.PILOT_SHA,
                pilot_scope_sha256=probe.PILOT_SCOPE_SHA, counts=probe.COUNTS, target=probe.TARGET,
                schedule=probe.order_plan(),
                inputs={cid: dict(relative_path=f"points/{cid}_8192.npz", sha256=h, partial_sha256=h)
                        for cid in (*probe.FOCAL, *probe.FILLERS)},
                historical={cid: dict(anchor_sha256=h, order_sha256=h, inverse_sha256=h) for cid in probe.FOCAL})


class Array:
    def __init__(self, value):
        self.value = np.asarray(value)
        self.shape = self.value.shape
        self.dtype = self.value.dtype
        self.device = "fixture"

    def __getitem__(self, i):
        return Array(self.value[i])

    def detach(self):
        return self

    def cpu(self):
        return self

    def contiguous(self):
        return self

    def numpy(self):
        return self.value


def lexicographic_order(xyz):
    x, y, z = xyz.value[0].T
    order = np.lexsort((np.arange(256), z, y, x))
    return Array(order[None]), Array(np.argsort(order)[None])


class Mixer:
    def __init__(self, training=False):
        self.training = training
        self.hook = None
        self.forward_count = 0

    def register_forward_pre_hook(self, hook):
        self.hook = hook
        return types.SimpleNamespace(remove=lambda: setattr(self, "hook", None))

    def forward(self, features, xyz):
        if self.hook:
            self.hook(self, (features, xyz))
        self.forward_count += 1
        raise AssertionError("target mixer ran")


class PrefixTest(unittest.TestCase):
    def test_frozen_factorial_slots_and_bounds(self):
        schedule = probe.order_plan()
        self.assertEqual(len(schedule), 16)
        self.assertEqual([r["call"] for r in schedule], list(range(1, 17)))
        for cid in probe.FOCAL:
            self.assertEqual(len({(r["model_seed"], r["mode"], r["layout"]) for r in schedule if r["case"] == cid}), 8)
            self.assertEqual(len({r["rng_seed"] for r in schedule if r["case"] == cid}), 2)
        for row in schedule:
            self.assertEqual(row["batch"][row["slot"]], row["case"])
            self.assertEqual(len(row["batch"]), 8 if row["layout"] == "batch8" else 1)
            self.assertEqual(len(set(row["batch"])), len(row["batch"]))
            if row["layout"] == "batch8":
                self.assertEqual(set(row["batch"]) - {row["case"]}, set(probe.FILLERS))

    def test_authorization_and_rejection(self):
        h, a = "a" * 64, "b" * 64
        q = make_scope()
        auth = dict(schema="bcsp-development-authorization-v1", request_sha256=h,
                    explicit_user_authorization=True, user_authorization_text="fixture")
        rt = dict(schema="bcsp-development-runtime-v1", request_sha256=h, authorization_sha256=a)
        with self.assertRaisesRegex(ValueError, "fresh server binding"):
            probe.authorize(q, h, auth, a, rt)
        q["status"] = "AWAITING_EXPLICIT_USER_AUTHORIZATION"
        probe.authorize(q, h, auth, a, rt)
        with self.assertRaisesRegex(ValueError, "runtime proof"):
            probe.authorize(q, h, auth, a, {**rt, "authorization_sha256": h})
        with self.assertRaisesRegex(ValueError, "single-use"):
            probe.authorize(q, h, {**auth, "request_sha256": a}, a, rt)
        q["schedule"][0]["batch"].append("wrong")
        with self.assertRaisesRegex(ValueError, "schedule"):
            probe.authorize(q, h, auth, a, rt)

    def test_stop_before_target_and_use_correct_batch_slot(self):
        row = next(r for r in probe.order_plan() if r["layout"] == "batch8" and r["mode"] == "train")
        m = Mixer(training=True)
        xyz = np.arange(8 * 256 * 3, dtype=np.float32).reshape(8, 256, 3)[:, ::-1]
        x = Array(np.zeros((8, 8192, 3), np.float32))
        features = Array(np.zeros((8, 256, 384), np.float32))
        backend = types.SimpleNamespace(float32=np.float32, no_grad=nullcontext,
                                        isfinite=lambda t: np.isfinite(t.value))
        coords, order, inverse = probe.observe(backend, lambda _: m.forward(features, Array(xyz)), m, x, row)
        np.testing.assert_array_equal(coords, xyz[row["slot"]])
        np.testing.assert_array_equal(order, np.arange(255, -1, -1))
        self.assertEqual(m.forward_count, 0)
        self.assertIsNone(m.hook)
        probe.array_hashes(np, (coords, order, inverse))
        with self.assertRaisesRegex(ValueError, "escaped"):
            probe.observe(backend, lambda _: None, m, x, row)
        self.assertIsNone(m.hook)

    def test_inverse_and_tie_guard(self):
        coords = np.zeros((256, 3), dtype=np.float32)
        ids = np.arange(256, dtype=np.int64)
        probe.array_hashes(np, (coords, ids, ids))
        with self.assertRaisesRegex(ValueError, "XYZ"):
            probe.array_hashes(np, (coords, ids[::-1], ids[::-1]))
        with self.assertRaisesRegex(ValueError, "inverse"):
            probe.array_hashes(np, (coords, ids, ids[::-1]))

    def test_cache_gate_and_historical_distinction(self):
        hist = make_scope()["historical"]
        rows = [dict(condition=r, hashes=hist[r["case"]].copy(), buffers_restored=True, rng_restored=True)
                for r in probe.order_plan()]
        self.assertEqual(probe.decide(rows, hist)["outcome"], "CONDITIONAL_CONTENT_KEYED_CACHE_PASS")
        changed = copy.deepcopy(rows)
        changed[0]["hashes"]["anchor_sha256"] = "b" * 64
        self.assertEqual(probe.decide(changed, hist)["outcome"], "DISABLE_PERMUTATION_CACHE_ONLINE_ONLY_PENDING")
        for row in changed:
            if row["condition"]["case"] == probe.FOCAL[0]:
                row["hashes"]["anchor_sha256"] = "b" * 64
        self.assertEqual(probe.decide(changed, hist)["outcome"], "HISTORICAL_ANCHOR_MISMATCH_REVALIDATE_BEFORE_P0C")
        with self.assertRaisesRegex(ValueError, "complete"):
            probe.decide(changed[:-1], hist)
        changed[0]["rng_restored"] = False
        with self.assertRaisesRegex(ValueError, "restoration"):
            probe.decide(changed, hist)

    def test_seed_adapter_changes_only_frozen_literal(self):
        path = Path("E:/ResearchBackups/AdaPoinTr/BCSP_CISC/2026-11-25_archive_v1/github_snapshot/archives/"
                    "cranial_bcsp_cisc_20261125_v1/bound_sources/69bfbf311e6b_bcsp_scq_prime_seeded_parent_v1.py")
        source = path.read_bytes()
        sha = probe.digest(source)
        self.assertEqual(sha, "69bfbf311e6b22e5e09ce45927ac784abfb184a0fd4e6054dff3820a69fa5250")
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_build")
        env = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), env)
        helper = types.SimpleNamespace(_source=lambda _fn, expected: (path, ast.parse(source)),
                                       _compile=lambda actual, _p, _g: actual)
        after = probe.seed_builder(types.SimpleNamespace(_build=env["_build"]), helper, sha)
        self.assertEqual(ast.dump(after), ast.dump(next(n for n in ast.parse(source.replace(
            b"(2026112101, 2026112102)", b"(2026112701, 2026112801)")).body
            if isinstance(n, ast.FunctionDef) and n.name == "_build")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
