import unittest

import numpy as np
from threadpoolctl import threadpool_limits

from rbss_geometry_v1 import (
    best_candidate,
    block_order,
    evaluate_candidate,
    fit_plane,
    invert,
    native_order,
    nearest,
    normal_for,
    plan_orders,
    plane_gates,
    reflected_edges,
    solve_control,
)


def winner(abc, cost=0.0, overlap=(1.0, 1.0)):
    return dict(abc=abc, valid=True, cost_mm=cost, overlap=overlap)


def known_plane():
    return dict(plane_ok=True, center_mm=[0, 0, 0], splits=[dict(best=winner((0, 0, 0)))])


def mirrored_points():
    rng = np.random.default_rng(1498)
    left = rng.uniform([25, -90, -65], [80, 90, 65], size=(512, 3))
    right = left * [-1, 1, 1]
    ordered_sides = np.stack((left, right), axis=1).reshape(-1, 3)
    return np.repeat(ordered_sides, 8, axis=0)


def grid_anchors(spacing):
    yz = np.array([(y * spacing, z * spacing) for y in range(16) for z in range(8)])
    left = np.column_stack((np.full(len(yz), 200), yz))
    return np.concatenate((left, left * [-1, 1, 1]))


class GeometryTest(unittest.TestCase):
    def test_exact_plane_and_coarse_refinement(self):
        points = mirrored_points()
        fit = fit_plane(points)
        self.assertTrue(fit["plane_ok"])
        for split in fit["splits"]:
            self.assertEqual(split["best"]["abc"], (0, 0, 0))
            self.assertLessEqual(split["best"]["cost_mm"], 1e-12)
            self.assertEqual((len(split["coarse"]), len(split["fine"])), (45, 27))

    def test_absent_midline_points_do_not_imply_failure(self):
        points = mirrored_points()
        self.assertTrue(np.all(np.abs(points[:, 0]) > 25))
        fit = fit_plane(points)
        self.assertTrue(fit["plane_ok"])
        self.assertEqual(fit["splits"][0]["best"]["counts"], [512, 512])

    def test_one_sided_candidate_invalid_and_wrong_axis_has_cost(self):
        points = mirrored_points()
        ids = (np.arange(0, 8192, 8), np.arange(1, 8192, 8))
        one_side = points.copy()
        one_side[:, 0] = np.abs(one_side[:, 0])
        self.assertFalse(any(r["valid"] for r in evaluate_candidate(one_side, one_side, (0, 0, 0), ids)))
        fit = evaluate_candidate(points, points, (0, 0, 0), ids)
        wrong = evaluate_candidate(points[:, [1, 0, 2]], points[:, [1, 0, 2]], (0, 0, 0), ids)
        self.assertGreater(wrong[0]["cost_mm"], fit[0]["cost_mm"])

    def test_plane_gates_boundary_agreement_and_quality(self):
        records = [winner((12, 0, 0), 6.1), winner((0, 0, 20), 0, (1.0, 0.44))]
        result = plane_gates(records)
        self.assertFalse(result["plane_ok"])
        self.assertEqual(set(result["reasons"]), {
            "A_SEARCH_BOUNDARY", "B_SEARCH_BOUNDARY", "A_HIGH_COST", "B_LOW_OVERLAP",
            "AB_OFFSET", "AB_ANGLE",
        })

    def test_ties_both_plane_and_duplicate_donors(self):
        self.assertEqual(best_candidate([winner((8, 0, 0), 2), winner((0, 0, 0), 2 + 0.9e-9)])["abc"], (0, 0, 0))
        self.assertEqual(best_candidate([winner((8, 0, 0), 2), winner((0, 0, 0), 2 + 1.1e-9)])["abc"], (8, 0, 0))
        query = np.array([[0., 0, 0]])
        donors = np.array([[1., 0, 0], [-1, 0, 0], [1, 0, 0]])
        dist, ids = nearest(query, donors, np.array([32, 45, 2]))
        np.testing.assert_array_equal(dist, [1.0])
        np.testing.assert_array_equal(ids, [2])
        gap, donor = nearest(query, donors[:0], np.array([], dtype=np.int64))
        self.assertTrue(np.isinf(gap[0]))
        self.assertEqual(donor[0], -1)

    def test_mirror_pair_selection_and_native_ties(self):
        xyz = np.array([[30., 0, 0], [-30, 0, 0], [-30, 0, 0], [1, 0, 0]])
        ends, left, right, _, _ = reflected_edges(xyz, xyz[:, 0], normal_for(0, 0), 4.0)
        np.testing.assert_array_equal(ends, [[0, 1]])
        np.testing.assert_array_equal(left, [0])
        np.testing.assert_array_equal(right, [1, 2])
        np.testing.assert_array_equal(native_order(xyz), [1, 2, 3, 0])

    def test_assignment_feasible_and_hall_deficiency(self):
        allowed = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=bool)
        cost = np.array([[0, 1, 8], [8, 0, 1], [1, 8, 0]], dtype=np.float64)
        row, col, total = solve_control(allowed, cost)
        np.testing.assert_array_equal(row, [0, 1, 2])
        np.testing.assert_array_equal(col, [1, 2, 0])
        self.assertEqual(total, 3_000_000)
        self.assertIsNone(solve_control(np.array([[1, 0, 0], [1, 0, 0], [0, 1, 1]], dtype=bool), cost))

    def test_inverse_and_block_rule(self):
        order = np.array([5, 3, 1, 2, 4, 0])
        grouped = block_order(order, [(1, 5), (4, 3)])
        np.testing.assert_array_equal(grouped, [5, 1, 3, 4, 2, 0])
        np.testing.assert_array_equal(grouped[invert(grouped)], np.arange(6))
        np.testing.assert_array_equal(invert(grouped)[grouped], np.arange(6))

    def test_joint_activation_same_endpoints_and_no_mirror_control(self):
        anchors = grid_anchors(10)
        result = plan_orders(anchors.astype(np.float32), anchors, known_plane())
        self.assertTrue(result["joint_active"], result["reasons"])
        self.assertEqual(result["k"], 128)
        s, c = result["s_edges"], result["c_edges"]
        for side in (0, 1):
            self.assertEqual({p[side] for p in s}, {p[side] for p in c})
        self.assertFalse({tuple(p) for p in s} & {tuple(p) for p in c})
        self.assertNotEqual(result["order"]["S"], result["order"]["C"])

    def test_common_fallback_without_perfect_matching(self):
        anchors = grid_anchors(0.05)
        result = plan_orders(anchors.astype(np.float32), anchors, known_plane())
        self.assertFalse(result["joint_active"])
        self.assertEqual(result["reasons"], ["NO_PERFECT_MATCH"])
        self.assertEqual(result["order"]["S"], result["order"]["R"])
        self.assertEqual(result["order"]["C"], result["order"]["R"])
        self.assertEqual(result["inverse"]["C"], result["inverse"]["S"])

    def test_common_fallback_on_duplicate_degenerate_anchors(self):
        anchors = np.zeros((256, 3))
        result = plan_orders(anchors.astype(np.float32), anchors, known_plane())
        self.assertEqual(result["reasons"], ["DEGENERATE_ANCHOR_SPACING"])
        self.assertEqual(len({tuple(o) for o in result["order"].values()}), 1)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        unittest.main(verbosity=2)
