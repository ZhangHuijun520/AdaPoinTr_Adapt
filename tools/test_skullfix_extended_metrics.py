#!/usr/bin/env python
"""Synthetic checks for extended SkullFix statistics and voxel metrics."""

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import (  # noqa: E402
    describe_values,
    paired_comparisons,
)
from utils.skullfix_metrics import point_rim_metrics  # noqa: E402
from utils.skullfix_voxel_metrics import (  # noqa: E402
    mask_metric_dict,
    splat_world_points_to_mask,
)


def assert_close(actual, expected, tolerance=1e-10):
    if not np.isclose(actual, expected, atol=tolerance, rtol=0):
        raise AssertionError(f"{actual} != {expected}")


def main():
    described = describe_values(
        [1.0, 2.0, 3.0],
        bootstrap_samples=200,
        seed=7,
    )
    assert_close(described["mean"], 2.0)
    assert_close(described["std"], 1.0)
    assert_close(described["median"], 2.0)

    comparisons = paired_comparisons(
        [
            {
                "final_cd_l1_mm": 1.0,
                "input_cd_l1_mm": 2.0,
                "final_surface_dice_at_1mm": 0.8,
                "input_surface_dice_at_1mm": 0.7,
                "final_rve": -0.1,
                "input_rve": -0.2,
            },
            {
                "final_cd_l1_mm": 3.0,
                "input_cd_l1_mm": 2.0,
                "final_surface_dice_at_1mm": 0.6,
                "input_surface_dice_at_1mm": 0.7,
                "final_rve": -0.3,
                "input_rve": -0.2,
            },
        ],
        bootstrap_samples=100,
    )
    assert_close(comparisons["cd_l1_mm"]["improvement_rate"], 0.5)
    assert comparisons["surface_dice_at_1mm"]["higher_is_better"]
    assert_close(
        comparisons["surface_dice_at_1mm"]["improvement_rate"], 0.5
    )
    assert (
        comparisons["rve"]["delta_definition"]
        == "abs(candidate)_minus_abs(baseline)"
    )
    assert_close(comparisons["rve"]["improvement_rate"], 0.5)

    reference_implant = np.asarray(
        [[0.0, y, 0.0] for y in range(5)], dtype=np.float64
    )
    defective = np.asarray(
        [[-1.0, y, 0.0] for y in range(5)], dtype=np.float64
    )
    rim = point_rim_metrics(
        reference_implant,
        reference_implant,
        defective,
        rim_band_mm=1.1,
        tolerances_mm=(0.5, 1.0),
    )
    assert_close(rim.contact_cd_l1_mm, 0.0)
    assert_close(rim.contact_nsd[0.5], 1.0)
    assert_close(rim.gt_rim_to_pred_mean_mm, 1.0)

    shape = (9, 9, 9)
    directions = np.eye(3, dtype=np.float64)
    origin = np.zeros(3, dtype=np.float64)
    reference_mask = np.zeros(shape, dtype=bool)
    reference_mask[4, 2:7, 2:7] = True
    reference_points = np.argwhere(reference_mask).astype(np.float64)

    identical_mask = splat_world_points_to_mask(
        reference_points,
        shape,
        directions,
        origin,
        radius_mm=0.0,
    )
    identical = mask_metric_dict(
        identical_mask,
        reference_mask,
        directions,
        origin,
        tolerances_mm=(0.5, 1.0),
    )
    assert_close(identical["dsc"], 1.0)
    assert_close(identical["surface_dice_at_0.5mm"], 1.0)
    assert_close(identical["surface_hd95_mm"], 0.0)

    shifted_mask = splat_world_points_to_mask(
        reference_points + np.asarray([1.0, 0.0, 0.0]),
        shape,
        directions,
        origin,
        radius_mm=0.0,
    )
    shifted = mask_metric_dict(
        shifted_mask,
        reference_mask,
        directions,
        origin,
        tolerances_mm=(0.5, 1.0),
    )
    assert_close(shifted["dsc"], 0.0)
    assert_close(shifted["surface_dice_at_0.5mm"], 0.0)
    assert_close(shifted["surface_dice_at_1mm"], 1.0)
    assert_close(shifted["surface_hd95_mm"], 1.0)

    print("[ok] statistics synthetic checks")
    print("[ok] point-rim synthetic checks")
    print("[ok] voxel identity and +1 mm checks")


if __name__ == "__main__":
    main()
