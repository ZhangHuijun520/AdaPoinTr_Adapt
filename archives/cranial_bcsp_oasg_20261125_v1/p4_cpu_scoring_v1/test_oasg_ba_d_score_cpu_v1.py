"""Artificial CPU verification of scoring, grouping, and frozen read contracts."""
import importlib.util
import io
from pathlib import Path
import unittest

import numpy as np
import oasg_ba_d_score_v1 as worker


def metrics():
    p = Path(__file__).resolve().parents[2] / "cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py"
    spec = importlib.util.spec_from_file_location("oasg_test_metrics", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Contract(unittest.TestCase):
    def test_area_weighted_coverage_dense_cd_and_strict_threshold(self):
        m = metrics()
        ref = {"a_centers": np.array([[0, 0, 0], [2, 0, 0], [30, 0, 0]]),
               "a_is_j": np.array([False, False, True]), "a_weights": np.array([1, 3, 1])}
        p = np.array([[0, 0, 0], [20, 0, 0], [21, 0, 0]])
        gt = np.array([[0, 0, 0], [30, 0, 0]])
        score, details, distance = worker.endpoint(m, p, ref, p[:1], gt, dense=True)
        self.assertEqual(score["E_Cover_at_2"], 1)
        self.assertEqual(score["J_P95_mm"], 9)
        self.assertAlmostEqual(score["far20"], 1 / 3)
        expected = .5 * (m.nearest(p, gt).mean() + m.nearest(gt, p).mean())
        self.assertEqual(score["CD_L1_mm"], expected)
        self.assertEqual(details["forward_A1"]["E"]["p95_mm"], 2)
        self.assertTrue(np.array_equal(distance, [0, 20, 21]))

    def test_far_child_partition_and_dense_severity(self):
        m = metrics()
        coarse = np.zeros((256, 3), dtype=np.float32)
        coarse[1, 0] = 30
        dense = np.repeat(coarse, 32, axis=0)
        dense[3, 0] = 25
        arr = dict(coarse=coarse, prediction=dense, parent_index=np.repeat(np.arange(256), 32))
        g = np.array([[0., 0, 0], [30, 1, 0]])
        ref = {"a_centers": np.array([[0., 0, 0], [30, 1, 0]]),
               "a_is_j": np.array([False, True]), "a_weights": np.ones(2)}
        r = worker.score_prediction(m, arr, ref, g[:1], g, dict(center=[0, 0, 0], scale=1.))
        self.assertEqual(r["geometry"]["far_parent_child"],
                         dict(near_parent_far_child=1, far_parent_far_child=32, far_children=33, children=8192))
        self.assertFalse(r["severe_geometry"])

    def test_verified_npz_fields_and_anchor_identity(self):
        x = np.zeros((256, 3), dtype=np.float32)
        i = np.arange(256, dtype=np.int64)
        arr = dict(coarse=x, prediction=np.repeat(x, 32, axis=0), S=x, delta=x,
                   token_index=i, parent_index=np.repeat(i, 32))
        def encode():
            b = io.BytesIO()
            np.savez(b, **arr)
            return b.getvalue()
        self.assertEqual(len(worker.decode_prediction(encode(), "A")), 6)
        arr["delta"] = x + 1
        with self.assertRaisesRegex(ValueError, "anchor"):
            worker.decode_prediction(encode(), "A")

    def test_105_pairs_source_bootstrap_and_severe_transitions(self):
        rows = []
        sources = [f"train:{i:03}" for i in range(21)]
        for i, src in enumerate(sources):
            for k in range(5):
                for arm in worker.ARMS:
                    v = dict(E_P95_mm=float(i - 1 if arm == "A" else i), J_Cover_at_2=.7 if arm == "A" else .6)
                    rows.append(dict(case_id=f"train__{i:03}__type{k}", source_id=src, arm=arm,
                                     coarse=v, dense=v, severe_geometry=(i == 0 and k == 0 and arm == "A")))
        idx = worker.bootstrap()
        self.assertEqual(idx.shape, (2000, 21))
        self.assertTrue(np.array_equal(idx, worker.bootstrap()))
        p, s = worker.summarize(rows, sources, idx)
        self.assertEqual(len(p), 105)
        self.assertEqual(s["metrics"]["dense"]["E_P95_mm"]["CI95"], [-1., -1.])
        self.assertAlmostEqual(s["metrics"]["coarse"]["J_Cover_at_2"]["delta_A_minus_B"], 10)
        self.assertEqual(s["severe_case_ids"]["new"], ["train__000__type0"])

    def test_exact_scoring_authorization(self):
        q = dict(schema=worker.SCHEMA, status=worker.STATUS, execution_authorized=False, counts=worker.COUNTS,
                 automatic_retry=False, formal_gate_executed_here=False)
        a = dict(schema=worker.SCHEMA + "-authorization", request_sha256="a" * 64,
                 explicit_user_authorization=True, user_authorization_text="fixture")
        worker.authorize(q, "a" * 64, a)
        with self.assertRaisesRegex(ValueError, "authorization"):
            worker.authorize(q, "b" * 64, a)


if __name__ == "__main__":
    unittest.main(verbosity=2)
