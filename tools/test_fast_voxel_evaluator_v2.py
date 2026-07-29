#!/usr/bin/env python
"""Check fast voxel evaluator parity with the legacy implementation."""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import nrrd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_ROOT = REPO_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from evaluate_skullfix_voxel_metrics import prefixed  # noqa: E402
from evaluate_skullfix_voxel_metrics_fast import (  # noqa: E402
    voxel_metrics_from_masks,
)
from utils.skullfix_voxel_metrics import (  # noqa: E402
    indices_to_world,
    mask_metric_dict,
    surface_world_points,
    voxel_rim_metric_dict,
)


def assert_metric_dict_equal(actual, expected):
    assert list(actual) == list(expected)
    for key in actual:
        actual_value = float(actual[key])
        expected_value = float(expected[key])
        if np.isnan(actual_value) and np.isnan(expected_value):
            continue
        assert actual_value == expected_value, (
            key,
            actual_value,
            expected_value,
        )


def synthetic_masks():
    shape = (25, 27, 29)
    grid = np.indices(shape).transpose(1, 2, 3, 0)
    center = np.asarray((12, 13, 14))
    complete = np.linalg.norm(grid - center, axis=-1) <= 9
    defect_region = (
        (grid[..., 0] >= 12)
        & (grid[..., 1] >= 11)
        & (grid[..., 2] >= 10)
    )
    implant = complete & defect_region
    defective = complete & ~defect_region
    prediction = np.roll(implant, shift=1, axis=0)
    prediction[0] = False
    return complete, defective, implant, prediction


def legacy_metric_values(
    prediction,
    complete,
    defective,
    implant,
    directions,
    origin,
    tolerances,
):
    final = defective | prediction
    values = {}
    values.update(
        prefixed(
            "implant",
            mask_metric_dict(
                prediction,
                implant,
                directions,
                origin,
                tolerances_mm=tolerances,
            ),
        )
    )
    values.update(
        prefixed(
            "final",
            mask_metric_dict(
                final,
                complete,
                directions,
                origin,
                tolerances_mm=tolerances,
            ),
        )
    )
    values.update(
        prefixed(
            "input",
            mask_metric_dict(
                defective,
                complete,
                directions,
                origin,
                tolerances_mm=tolerances,
            ),
        )
    )
    values.update(
        prefixed(
            "rim",
            voxel_rim_metric_dict(
                prediction,
                implant,
                defective,
                directions,
                origin,
                rim_band_mm=2.0,
                tolerances_mm=tolerances,
            ),
        )
    )
    return values


def test_surface_reuse_parity():
    complete, defective, implant, prediction = synthetic_masks()
    directions = np.diag((0.8, 1.1, 1.4))
    origin = np.asarray((3.0, -2.0, 4.5))
    tolerances = (0.5, 1.0, 2.0)
    expected = legacy_metric_values(
        prediction,
        complete,
        defective,
        implant,
        directions,
        origin,
        tolerances,
    )
    actual = voxel_metrics_from_masks(
        prediction,
        complete,
        defective,
        implant,
        directions,
        origin,
        rim_band_mm=2.0,
        tolerances_mm=tolerances,
    )
    assert_metric_dict_equal(actual, expected)


def write_integration_fixture(root):
    raw_dir = root / "raw"
    prediction_dir = root / "predictions"
    raw_dir.mkdir()
    prediction_dir.mkdir()
    complete, defective, implant, prediction = synthetic_masks()
    directions = np.diag((0.8, 1.1, 1.4))
    origin = np.asarray((3.0, -2.0, 4.5))
    header = {
        "space directions": directions,
        "space origin": origin,
    }
    raw_paths = {}
    for role, mask in (
        ("complete", complete),
        ("defective", defective),
        ("implant", implant),
    ):
        path = raw_dir / f"{role}.nrrd"
        nrrd.write(
            str(path),
            mask.astype(np.uint8),
            header=header,
            index_order="F",
        )
        raw_paths[role] = str(path)

    prediction_indices = np.argwhere(
        np.asarray(prediction, dtype=bool)
    )
    prediction_world = indices_to_world(
        prediction_indices,
        directions,
        origin,
    )
    records = []
    for index in range(2):
        prediction_path = prediction_dir / f"prediction_{index}.npz"
        np.savez_compressed(
            prediction_path,
            prediction_implant=prediction_world,
            centroid=np.zeros(3, dtype=np.float64),
            scale=np.asarray(1.0, dtype=np.float64),
        )
        records.append(
            {
                "case_id": f"case_{index}",
                "split": "test",
                "skull_id": f"skull_{index}",
                "defect_type": "synthetic",
                "prediction_path": prediction_path.name,
                "raw": raw_paths,
            }
        )
    manifest = prediction_dir / "predictions_manifest.jsonl"
    manifest.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )
    return manifest, raw_dir


def run_command(arguments):
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(
            f"command failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result


def csv_rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def comparable_summary(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload.pop("per_sample_csv", None)
    return payload


def test_cli_parallel_and_resume_parity():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        manifest, raw_dir = write_integration_fixture(root)
        legacy_out = root / "legacy"
        fast_out = root / "fast"
        common = [
            "--prediction_manifest",
            str(manifest),
            "--raw_root",
            str(raw_dir),
            "--splat_radius_mm",
            "0",
            "--rim_band_mm",
            "2",
            "--bootstrap_samples",
            "50",
            "--seed",
            "17",
            "--dataset_label",
            "Synthetic",
            "--output_prefix",
            "parity",
        ]
        run_command(
            [
                "tools/evaluate_skullfix_voxel_metrics.py",
                *common,
                "--out_dir",
                str(legacy_out),
            ]
        )
        first_fast = run_command(
            [
                "tools/evaluate_skullfix_voxel_metrics_fast.py",
                *common,
                "--out_dir",
                str(fast_out),
                "--num_workers",
                "2",
            ]
        )
        assert "computed=2 cached=0 workers=2" in first_fast.stdout

        legacy_csv = legacy_out / "parity_voxel_per_sample.csv"
        fast_csv = fast_out / "parity_voxel_per_sample.csv"
        assert csv_rows(fast_csv) == csv_rows(legacy_csv)
        assert comparable_summary(
            fast_out / "parity_voxel_summary.json"
        ) == comparable_summary(
            legacy_out / "parity_voxel_summary.json"
        )

        second_fast = run_command(
            [
                "tools/evaluate_skullfix_voxel_metrics_fast.py",
                *common,
                "--out_dir",
                str(fast_out),
                "--num_workers",
                "2",
            ]
        )
        assert "computed=0 cached=2 workers=1" in second_fast.stdout
        timing = json.loads(
            (fast_out / "parity_voxel_timing.json").read_text(
                encoding="utf-8"
            )
        )
        assert timing["cached_cases"] == 2
        assert timing["computed_cases"] == 0


def main():
    test_surface_reuse_parity()
    print("[ok] reused surfaces are exactly equal to legacy metrics")
    test_cli_parallel_and_resume_parity()
    print("[ok] parallel CLI CSV and summary equal legacy output")
    print("[ok] signed per-case resume cache")


if __name__ == "__main__":
    main()
