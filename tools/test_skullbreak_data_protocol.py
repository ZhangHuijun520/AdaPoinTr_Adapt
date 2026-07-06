#!/usr/bin/env python
"""Synthetic checks for SkullBreak grouping and grouped statistics."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import nrrd

from check_skullbreak_pointcloud import validate_grouping
from prepare_skullbreak_pointcloud import (
    DEFECT_TYPES,
    assign_group_splits,
    index_skulls,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.evaluation_statistics import (  # noqa: E402
    aggregate_rows_by_group,
    describe_rows_by_group,
)


def make_raw_tree(root, skull_names):
    complete_root = root / "complete_skull"
    for role in ("complete_skull", "defective_skull", "implant"):
        (root / role).mkdir(parents=True, exist_ok=True)
    for skull_name in skull_names:
        (complete_root / f"{skull_name}.nrrd").touch()
        for defect_type in DEFECT_TYPES:
            for role in ("defective_skull", "implant"):
                directory = root / role / defect_type
                directory.mkdir(parents=True, exist_ok=True)
                (directory / f"{skull_name}.nrrd").touch()


def write_synthetic_nrrd_tree(root, skull_name, offset):
    shape = (20, 20, 20)
    complete = np.zeros(shape, dtype=np.uint8)
    complete[3 + offset : 17 + offset, 3:17, 3:17] = 1
    header = {
        "space directions": np.eye(3, dtype=np.float64) * 0.4,
        "space origin": np.asarray([-4.0, -4.0, -4.0]),
    }

    complete_dir = root / "complete_skull"
    complete_dir.mkdir(parents=True, exist_ok=True)
    nrrd.write(
        str(complete_dir / f"{skull_name}.nrrd"),
        complete,
        header=header,
        index_order="F",
    )
    for defect_index, defect_type in enumerate(DEFECT_TYPES):
        implant = np.zeros_like(complete)
        start = 4 + defect_index
        implant[start : start + 3, 7:13, 7:13] = complete[
            start : start + 3, 7:13, 7:13
        ]
        defective = complete & ~implant
        for role, volume in (
            ("defective_skull", defective),
            ("implant", implant),
        ):
            directory = root / role / defect_type
            directory.mkdir(parents=True, exist_ok=True)
            nrrd.write(
                str(directory / f"{skull_name}.nrrd"),
                volume.astype(np.uint8),
                header=header,
                index_order="F",
            )


def check_end_to_end_conversion(root):
    training_root = root / "training"
    evaluation_root = root / "evaluation"
    output_root = root / "pointcloud"
    write_synthetic_nrrd_tree(training_root, "train_001", 0)
    write_synthetic_nrrd_tree(evaluation_root, "test_001", 1)

    command = [
        sys.executable,
        str(REPO_ROOT / "tools" / "prepare_skullbreak_pointcloud.py"),
        "--training_root",
        str(training_root),
        "--evaluation_root",
        str(evaluation_root),
        "--output_root",
        str(output_root),
        "--n_complete",
        "64",
        "--n_partial",
        "64",
        "--n_implant",
        "32",
        "--expected_train_skulls",
        "1",
        "--expected_test_skulls",
        "1",
        "--monitor_skulls",
        "1",
        "--workers",
        "2",
        "--strict_geometry",
        "--strict_quality",
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)

    records = [
        json.loads(line)
        for line in (output_root / "manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(records) == 10
    assert validate_grouping(records, 1, 1) == {
        "train": 1,
        "test": 1,
    }
    for record in records:
        with np.load(output_root / record["point_path"]) as sample:
            assert sample["partial"].shape == (64, 3)
            assert sample["gt"].shape == (64, 3)
            assert sample["implant"].shape == (32, 3)
            assert np.isfinite(sample["partial"]).all()

    development_output = root / "pointcloud_training_only"
    development_command = [
        sys.executable,
        str(REPO_ROOT / "tools" / "prepare_skullbreak_pointcloud.py"),
        "--training_root",
        str(training_root),
        "--output_root",
        str(development_output),
        "--n_complete",
        "32",
        "--n_partial",
        "32",
        "--n_implant",
        "16",
        "--expected_train_skulls",
        "1",
        "--expected_test_skulls",
        "0",
    ]
    subprocess.run(
        development_command,
        check=True,
        capture_output=True,
        text=True,
    )
    development_records = [
        line
        for line in (development_output / "manifest.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert len(development_records) == 5


def synthetic_records():
    records = []
    for official_split, skull_id, complete_hash, gate_split in (
        ("train", "train:a", "hash-a", "train"),
        ("train", "train:b", "hash-b", "val"),
        ("test", "test:c", "hash-c", "official_test"),
    ):
        for defect_type in DEFECT_TYPES:
            records.append(
                {
                    "skull_id": skull_id,
                    "official_split": official_split,
                    "gate_split": gate_split,
                    "defect_type": defect_type,
                    "complete_mask_sha256": complete_hash,
                }
            )
    return records


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        make_raw_tree(root, ("001", "002"))
        groups = index_skulls(root, "train")
        assert len(groups) == 2
        assert all(len(group["cases"]) == 5 for group in groups)
        assert {
            case["defect_type"] for case in groups[0]["cases"]
        } == set(DEFECT_TYPES)
        check_end_to_end_conversion(root / "end_to_end")

    skull_ids = [f"train:{index:03d}" for index in range(10)]
    assignments, counts, shuffled = assign_group_splits(
        skull_ids, "0.8,0.1,0.1", 7
    )
    assert counts == {"train": 8, "val": 1, "test": 1}
    assert len(assignments) == len(skull_ids)
    assert len(shuffled) == len(skull_ids)

    records = synthetic_records()
    split_skulls = validate_grouping(records, 2, 1)
    assert split_skulls == {"train": 2, "test": 1}

    leaking = [dict(record) for record in records]
    leaking[-1]["complete_mask_sha256"] = "hash-a"
    try:
        validate_grouping(leaking, 2, 1)
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected complete-skull hash leakage failure")

    metric_rows = [
        {"skull_id": "a", "defect_type": "bilateral", "cd": 1.0},
        {"skull_id": "a", "defect_type": "random_1", "cd": 3.0},
        {"skull_id": "b", "defect_type": "bilateral", "cd": 8.0},
    ]
    skull_rows = aggregate_rows_by_group(metric_rows, "skull_id", ["cd"])
    assert len(skull_rows) == 2
    assert np.isclose(skull_rows[0]["cd"], 2.0)
    grouped = describe_rows_by_group(
        metric_rows,
        "defect_type",
        ["cd"],
        bootstrap_samples=0,
    )
    assert grouped["bilateral"]["num_cases"] == 2
    assert np.isclose(
        grouped["bilateral"]["statistics"]["cd"]["mean"], 4.5
    )

    print("[ok] exact five-defect indexing")
    print("[ok] end-to-end NRRD to NPZ conversion")
    print("[ok] skull-level split isolation and hash leakage checks")
    print("[ok] skull-macro and defect-stratified statistics")


if __name__ == "__main__":
    main()
