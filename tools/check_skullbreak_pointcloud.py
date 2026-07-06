#!/usr/bin/env python
"""Validate SkullBreak grouping, split isolation, NPZ files, and checksums."""

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

DEFECT_TYPES = {
    "bilateral",
    "frontoorbital",
    "parietotemporal",
    "random_1",
    "random_2",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", type=Path, required=True)
    parser.add_argument("--manifest", default="manifest.jsonl")
    parser.add_argument("--max_samples", type=int)
    parser.add_argument("--expected_train_skulls", type=int, default=114)
    parser.add_argument("--expected_test_skulls", type=int, default=20)
    parser.add_argument("--verify_checksums", action="store_true")
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_grouping(records, expected_train_skulls, expected_test_skulls):
    official_by_skull = defaultdict(set)
    gate_by_skull = defaultdict(set)
    defects_by_skull = defaultdict(set)
    hashes_by_official_split = defaultdict(set)

    for record in records:
        skull_id = str(record["skull_id"])
        official_by_skull[skull_id].add(record["official_split"])
        if record["official_split"] == "train":
            gate_by_skull[skull_id].add(record["gate_split"])
        defects_by_skull[skull_id].add(record["defect_type"])
        hashes_by_official_split[record["official_split"]].add(
            record["complete_mask_sha256"]
        )

    leaking_official = {
        skull_id: values
        for skull_id, values in official_by_skull.items()
        if len(values) != 1
    }
    if leaking_official:
        raise ValueError(
            f"Skulls cross official splits: {leaking_official}"
        )
    leaking_gate = {
        skull_id: values
        for skull_id, values in gate_by_skull.items()
        if len(values) != 1
    }
    if leaking_gate:
        raise ValueError(f"Skulls cross gate splits: {leaking_gate}")

    bad_defects = {
        skull_id: sorted(values)
        for skull_id, values in defects_by_skull.items()
        if values != DEFECT_TYPES
    }
    if bad_defects:
        raise ValueError(
            "Every skull must have exactly five defect types: "
            f"{bad_defects}"
        )

    hash_overlap = hashes_by_official_split["train"].intersection(
        hashes_by_official_split["test"]
    )
    if hash_overlap:
        raise ValueError(
            "Complete skull mask hashes overlap across official train/test: "
            f"{sorted(hash_overlap)}"
        )

    split_skulls = Counter(
        next(iter(values)) for values in official_by_skull.values()
    )
    if expected_train_skulls > 0 and split_skulls["train"] != expected_train_skulls:
        raise ValueError(
            f"Expected {expected_train_skulls} train skulls, "
            f"found {split_skulls['train']}"
        )
    if expected_test_skulls > 0 and split_skulls["test"] != expected_test_skulls:
        raise ValueError(
            f"Expected {expected_test_skulls} test skulls, "
            f"found {split_skulls['test']}"
        )
    return split_skulls


def load_expected_checksums(path):
    expected = {}
    for line in path.read_text(encoding="ascii").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(maxsplit=1)
        expected[relative.strip()] = digest
    return expected


def main():
    args = parse_args()
    data_root = args.data_root.expanduser().resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = data_root / manifest_path
    records = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError("Manifest contains no records")

    split_skulls = validate_grouping(
        records,
        args.expected_train_skulls,
        args.expected_test_skulls,
    )
    records_to_check = (
        records[: args.max_samples]
        if args.max_samples is not None
        else records
    )
    min_xyz = np.full(3, np.inf)
    max_xyz = np.full(3, -np.inf)
    implant_ious = []
    official_cases = Counter()
    gate_cases = Counter()
    defect_cases = Counter()

    expected_checksums = {}
    if args.verify_checksums:
        expected_checksums = load_expected_checksums(
            data_root / "SHA256SUMS"
        )

    for record in records_to_check:
        point_path = Path(record["point_path"])
        if not point_path.is_absolute():
            point_path = data_root / point_path
        if not point_path.is_file():
            raise FileNotFoundError(point_path)
        if args.verify_checksums:
            relative = record["point_path"]
            if sha256_file(point_path) != expected_checksums.get(relative):
                raise ValueError(f"Checksum mismatch: {relative}")

        with np.load(point_path, allow_pickle=False) as sample:
            expected = {
                "partial": (int(record["n_partial"]), 3),
                "gt": (int(record["n_complete"]), 3),
                "implant": (int(record["n_implant"]), 3),
            }
            for key, shape in expected.items():
                points = sample[key]
                if points.shape != shape:
                    raise ValueError(
                        f"{record['case_id']} {key}: "
                        f"expected {shape}, got {points.shape}"
                    )
                if points.dtype != np.float32:
                    raise ValueError(
                        f"{record['case_id']} {key}: "
                        f"expected float32, got {points.dtype}"
                    )
                if not np.isfinite(points).all():
                    raise ValueError(
                        f"{record['case_id']} {key}: NaN or Inf found"
                    )
                min_xyz = np.minimum(min_xyz, points.min(axis=0))
                max_xyz = np.maximum(max_xyz, points.max(axis=0))

        official_cases[record["official_split"]] += 1
        gate_cases[record["gate_split"]] += 1
        defect_cases[record["defect_type"]] += 1
        implant_ious.append(record["quality"]["implant_missing_iou"])

    print("==== SkullBreak point-cloud check ====")
    print(f"manifest: {manifest_path}")
    print(f"records_total: {len(records)}")
    print(f"records_checked: {len(records_to_check)}")
    print(f"official_skulls: {dict(sorted(split_skulls.items()))}")
    print(f"official_cases_checked: {dict(sorted(official_cases.items()))}")
    print(f"gate_cases_checked: {dict(sorted(gate_cases.items()))}")
    print(f"defect_cases_checked: {dict(sorted(defect_cases.items()))}")
    print(f"xyz_min: {min_xyz.tolist()}")
    print(f"xyz_max: {max_xyz.tolist()}")
    print(f"implant_missing_iou_min: {min(implant_ious):.6f}")
    print(f"implant_missing_iou_mean: {np.mean(implant_ious):.6f}")
    print("official_train_test_complete_hash_overlap: 0")
    print("[ok] SkullBreak grouping and point clouds are valid")


if __name__ == "__main__":
    main()
