import importlib.util
import unittest
from pathlib import Path

import numpy as np


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "prepare_skullfix_pointcloud.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_skullfix", SCRIPT_PATH)
PREPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARE)


class SkullFixPreparationTest(unittest.TestCase):
    def test_case_id_normalization(self):
        self.assertEqual(
            PREPARE.canonical_case_id(Path("complete_skull_001.nrrd")),
            "001",
        )
        self.assertEqual(
            PREPARE.canonical_case_id(
                Path("Case_007/complete.nrrd"),
                Path("."),
            ),
            "case_007",
        )

    def test_split_counts(self):
        self.assertEqual(
            PREPARE.parse_split_spec("80,10,10", 100),
            {"train": 80, "val": 10, "test": 10},
        )
        self.assertEqual(
            sum(PREPARE.parse_split_spec("0.8,0.1,0.1", 7).values()),
            7,
        )

    def test_triplet_metrics_and_shared_normalization(self):
        shape = (24, 20, 16)
        grid = np.indices(shape)
        center = (np.asarray(shape) - 1)[:, None, None, None] / 2
        radius = np.sqrt(((grid - center) ** 2).sum(axis=0))
        complete = (radius <= 8) & (radius >= 6)
        defective = complete & ~((grid[0] > 15) & (grid[1] > 8))
        implant = complete & ~defective

        metrics = PREPARE.triplet_metrics(complete, defective, implant)
        self.assertEqual(metrics["implant_missing_iou"], 1.0)
        self.assertEqual(metrics["reconstruction_iou"], 1.0)

        flat_indices = PREPARE.surface_flat_indices(complete)
        directions = np.diag([0.4, 0.4, 1.0])
        origin = np.array([10.0, -5.0, 2.0])
        centroid, scale = PREPARE.surface_normalization(
            flat_indices,
            shape,
            directions,
            origin,
        )
        points = PREPARE.sample_surface(
            flat_indices,
            shape,
            directions,
            origin,
            256,
            centroid,
            scale,
            np.random.RandomState(1),
        )
        self.assertEqual(points.shape, (256, 3))
        self.assertEqual(points.dtype, np.float32)
        self.assertTrue(np.isfinite(points).all())
        self.assertLessEqual(np.linalg.norm(points, axis=1).max(), 1.00001)


if __name__ == "__main__":
    unittest.main()
