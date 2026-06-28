#!/usr/bin/env python
"""Validate prepared SkullFix NPZ files without importing the training stack."""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_root", type=Path, required=True)
    parser.add_argument("--manifest", default="manifest.jsonl")
    parser.add_argument("--max_samples", type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    data_root = args.data_root.expanduser().resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = data_root / manifest_path

    records = []
    with open(manifest_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    if args.max_samples is not None:
        records = records[: args.max_samples]
    if not records:
        raise ValueError("Manifest contains no records")

    split_counts = Counter()
    min_xyz = np.full(3, np.inf)
    max_xyz = np.full(3, -np.inf)
    implant_ious = []

    for record in records:
        point_path = Path(record["point_path"])
        if not point_path.is_absolute():
            point_path = data_root / point_path
        if not point_path.is_file():
            raise FileNotFoundError(point_path)

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
                        f"{record['case_id']} {key}: expected {shape}, got {points.shape}"
                    )
                if points.dtype != np.float32:
                    raise ValueError(
                        f"{record['case_id']} {key}: expected float32, got {points.dtype}"
                    )
                if not np.isfinite(points).all():
                    raise ValueError(f"{record['case_id']} {key}: NaN or Inf found")
                min_xyz = np.minimum(min_xyz, points.min(axis=0))
                max_xyz = np.maximum(max_xyz, points.max(axis=0))

        split_counts[record["split"]] += 1
        implant_ious.append(record["quality"]["implant_missing_iou"])

    print("==== SkullFix point-cloud check ====")
    print(f"manifest: {manifest_path}")
    print(f"samples_checked: {len(records)}")
    print(f"split_counts: {dict(sorted(split_counts.items()))}")
    print(f"xyz_min: {min_xyz.tolist()}")
    print(f"xyz_max: {max_xyz.tolist()}")
    print(f"implant_missing_iou_min: {min(implant_ious):.6f}")
    print(f"implant_missing_iou_mean: {np.mean(implant_ious):.6f}")
    print("[ok] all checked point-cloud files are valid")


if __name__ == "__main__":
    main()
