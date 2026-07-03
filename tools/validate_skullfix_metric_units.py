#!/usr/bin/env python
"""Validate SkullFix millimeter metrics with analytic synthetic examples."""

import argparse
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.skullfix_metrics import (  # noqa: E402
    normalized_point_surface_metrics,
    normalized_to_world,
    point_surface_metrics,
    world_to_normalized,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run analytic tests for CD-L1, ASSD, HD95, NSD, and SkullFix "
            "normalized-to-world coordinate restoration."
        )
    )
    parser.add_argument(
        "--data_root",
        type=Path,
        default=Path("data/SkullFixPC"),
        help="Optional prepared SkullFix root used for a real-NPZ round-trip check.",
    )
    parser.add_argument(
        "--skip_real_sample",
        action="store_true",
        help="Run only synthetic tests.",
    )
    return parser.parse_args()


def assert_close(actual, expected, name, atol=1e-9):
    if not np.isclose(actual, expected, rtol=0.0, atol=atol):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def assert_array_close(actual, expected, name, atol=1e-9):
    if not np.allclose(actual, expected, rtol=0.0, atol=atol):
        error = float(np.max(np.abs(np.asarray(actual) - np.asarray(expected))))
        raise AssertionError(f"{name}: max absolute error {error} exceeds {atol}")


def separated_cube_points():
    return np.asarray(
        [
            [x, y, z]
            for x in (0.0, 10.0)
            for y in (0.0, 10.0)
            for z in (0.0, 10.0)
        ],
        dtype=np.float64,
    )


def test_identity():
    reference = separated_cube_points()
    metrics = point_surface_metrics(reference.copy(), reference)
    assert_close(metrics.cd_l1_mm, 0.0, "identity CD-L1")
    assert_close(metrics.assd_mm, 0.0, "identity ASSD")
    assert_close(metrics.hd95_mm, 0.0, "identity HD95")
    for tolerance, value in metrics.nsd.items():
        assert_close(value, 1.0, f"identity NSD@{tolerance:g}mm")
    print("[pass] identity: CD=ASSD=HD95=0 mm, NSD=1")


def test_one_mm_translation():
    reference = separated_cube_points()
    prediction = reference + np.asarray([1.0, 0.0, 0.0])
    metrics = point_surface_metrics(
        prediction,
        reference,
        tolerances_mm=(0.5, 1.0, 2.0),
    )
    assert_close(metrics.cd_l1_mm, 1.0, "1 mm translation CD-L1")
    assert_close(metrics.assd_mm, 1.0, "1 mm translation ASSD")
    assert_close(metrics.hd95_mm, 1.0, "1 mm translation HD95")
    assert_close(metrics.nsd[0.5], 0.0, "1 mm translation NSD@0.5mm")
    assert_close(metrics.nsd[1.0], 1.0, "1 mm translation NSD@1mm")
    assert_close(metrics.nsd[2.0], 1.0, "1 mm translation NSD@2mm")
    print("[pass] +1 mm: CD=ASSD=HD95=1 mm, NSD@0.5=0, NSD@1/2=1")


def test_normalization_round_trip():
    world = separated_cube_points() + np.asarray([35.0, -12.0, 104.0])
    centroid = np.asarray([12.5, -7.25, 101.0])
    scale = 97.3
    normalized = world_to_normalized(world, centroid, scale)
    restored = normalized_to_world(normalized, centroid, scale)
    assert_array_close(restored, world, "synthetic normalization round-trip")

    shifted_normalized = normalized + np.asarray([1.0 / scale, 0.0, 0.0])
    metrics = normalized_point_surface_metrics(
        shifted_normalized,
        normalized,
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    )
    assert_close(metrics.cd_l1_mm, 1.0, "normalized +1 mm CD-L1")
    assert_close(metrics.assd_mm, 1.0, "normalized +1 mm ASSD")
    assert_close(metrics.hd95_mm, 1.0, "normalized +1 mm HD95")
    assert_close(metrics.nsd[0.5], 0.0, "normalized +1 mm NSD@0.5mm")
    assert_close(metrics.nsd[1.0], 1.0, "normalized +1 mm NSD@1mm")
    print("[pass] normalization: round-trip exact and normalized shift restores to 1 mm")


def first_npz(data_root):
    points_dir = data_root.expanduser().resolve() / "points"
    candidates = sorted(points_dir.glob("*.npz"))
    if not candidates:
        raise FileNotFoundError(f"No prepared SkullFix NPZ files found in {points_dir}")
    return candidates[0]


def test_real_npz(data_root):
    sample_path = first_npz(data_root)
    with np.load(sample_path, allow_pickle=False) as sample:
        centroid = sample["centroid"]
        scale = sample["scale"]
        clouds = {
            key: sample[key].astype(np.float64)
            for key in ("partial", "gt", "implant")
        }

    max_round_trip_error = 0.0
    for name, normalized in clouds.items():
        restored = normalized_to_world(normalized, centroid, scale)
        round_trip = world_to_normalized(restored, centroid, scale)
        max_round_trip_error = max(
            max_round_trip_error,
            float(np.max(np.abs(round_trip - normalized))),
        )
        assert_array_close(
            round_trip,
            normalized,
            f"real NPZ {name} round-trip",
            atol=1e-12,
        )

    normalized_metrics = point_surface_metrics(
        clouds["implant"],
        clouds["gt"],
        tolerances_mm=(0.5 / float(scale), 1.0 / float(scale), 2.0 / float(scale)),
    )
    world_metrics = normalized_point_surface_metrics(
        clouds["implant"],
        clouds["gt"],
        centroid,
        scale,
        tolerances_mm=(0.5, 1.0, 2.0),
    )
    assert_close(
        world_metrics.cd_l1_mm,
        normalized_metrics.cd_l1_mm * float(scale),
        "real NPZ CD scale relation",
        atol=1e-10,
    )
    assert_close(
        world_metrics.assd_mm,
        normalized_metrics.assd_mm * float(scale),
        "real NPZ ASSD scale relation",
        atol=1e-10,
    )
    assert_close(
        world_metrics.hd95_mm,
        normalized_metrics.hd95_mm * float(scale),
        "real NPZ HD95 scale relation",
        atol=1e-10,
    )
    for world_tolerance, normalized_tolerance in (
        (0.5, 0.5 / float(scale)),
        (1.0, 1.0 / float(scale)),
        (2.0, 2.0 / float(scale)),
    ):
        assert_close(
            world_metrics.nsd[world_tolerance],
            normalized_metrics.nsd[normalized_tolerance],
            f"real NPZ NSD@{world_tolerance:g}mm scale relation",
        )

    print(f"[pass] real NPZ: {sample_path}")
    print(f"       centroid={np.asarray(centroid).tolist()}")
    print(f"       scale={float(scale):.9f} mm per normalized unit")
    print(f"       max_round_trip_error={max_round_trip_error:.3e}")
    print(
        "       implant-vs-complete diagnostic: "
        f"CD={world_metrics.cd_l1_mm:.6f} mm, "
        f"ASSD={world_metrics.assd_mm:.6f} mm, "
        f"HD95={world_metrics.hd95_mm:.6f} mm"
    )


def main():
    args = parse_args()
    print("==== SkullFix metric unit validation ====")
    test_identity()
    test_one_mm_translation()
    test_normalization_round_trip()
    if not args.skip_real_sample:
        test_real_npz(args.data_root)
    print("[ok] all SkullFix millimeter metric checks passed")


if __name__ == "__main__":
    main()
